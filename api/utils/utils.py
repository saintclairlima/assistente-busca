from chromadb import chromadb, Documents, EmbeddingFunction, Embeddings
import requests
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from torch import cuda

import httpx
import json
from api.configuracoes.config_gerais import configuracoes
from typing import Any, AsyncGenerator, Dict, Iterator, List, Tuple

# Data model for chat interactions
class DadosChat(BaseModel):
    '''
    Classe que modela uma interação com o chat

    Atributos:
        pergunta (str): pergunta do usuário
        histórico (List[str]): histórico com as últimas interações
    '''
    pergunta: str
    historico: list

class FuncaoEmbeddings(EmbeddingFunction):
    # Custom embedding function using a transformer model
    '''
    Função de embeddings customizada, a ser utilizada com um modelo baseado em Transformer

    Atributos:
        device (str): Tipo de dispositivo em que será executada a aplicação ['cuda', 'cpu']
        modelo (classe baseada em transformer): modelo pré-treinado
        instrucao (str): instrução a ser utilizada em modelos do tipo instructor
    '''

    def __init__(self, nome_modelo: str, tipo_modelo=SentenceTransformer, device: str=None, instrucao: str=None):
        '''
        Inicializa a função

        Parâmetros:
            nome_modelo (str): nome do modelo utilizado
            tipo_modelo (type): classe que encapsula o modelo utilizado
            device (str): parâmetro opcional, tipo de dispositivo em que será executada a aplicação ['cuda', 'cpu']
            instrucao (str): parâmetro opcional, instrução a ser utilizada em modelos do tipo instructor
        '''

        # Caso não seja informado o dispositivo/device, utiliza 'cuda'/'cpu' de acordo com o que está disponível
        if device:
            self.device = device
        else:
            self.device = 'cuda' if cuda.is_available() else 'cpu'

        # Carrega modelo pré-treinado com remote code trust habilitado
        self.modelo = tipo_modelo(nome_modelo, device=self.device, cache_folder=configuracoes.url_cache_modelos, trust_remote_code=True)
        self.modelo.to(self.device)
        self.instrucao = instrucao

    def __call__(self, input: Documents) -> Embeddings:
        '''
        Gera embeddings para uma coleção de documentos

        Parâmetros:
            input (chromadb.Documents): uma lista de strings com o conteúdo a ser representado por embeddings
        
        Retorna:
            (chroma.Embeddings): uma lista de representações de Embeddings (List[ndarray[Any, dtype[signedinteger[_32Bit] | floating[_32Bit]]]])
        '''

        # Generate embeddings for input text
        if self.instrucao:
            input_instrucao = [(self.instrucao, doc) for doc in input]
            embeddings = self.modelo.encode(input_instrucao, convert_to_numpy=True, device=self.device)
        else:
            embeddings = self.modelo.encode(input, convert_to_numpy=True, device=self.device)
        return embeddings.tolist()
    
class ClienteLLM:
    # Base client class for LLM interactions
    '''
    Classe base a ser utilizada em interações com um LLM em uma API

    Atributos:
        modelo (str): nome do modelo a ser utilizado
        url_llm (str): url onde a API do LLM se encontra
        temperature (float): temperatura do modelo. Valores altos fazem o modelo responder de forma mais criativa
        top_k (int): Reduz a probabilidade de gerar alucinação. Valores altos (ex. 100) resultam em respostas com diversidade; valores baixos (ex. 10) são mais conservadores
        top_p (float): ATua junto com top_k. Valores altos (ex. 0.95) resultam em texto mais diverso; valores baixos (ex. 0.5) geram texto mais conservador e focado.

    Métodos:
        health(): teste simples de verificação se a API está ativa
        stream(mensagens: List[dict]): Envia solicitação ao endpoint de geração de texto usando a opção de 'stream' (obtendo a resposta em framentos)
    '''

    def __init__(self, nome_modelo: str, url_llm: str, temperature: float=configuracoes.temperature, top_k: int=configuracoes.top_k, top_p: float=configuracoes.top_p):

        self.modelo = nome_modelo
        self.url_llm = url_llm
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
    
    async def stream(self, mensagens: List[dict]):
        raise NotImplementedError('Método stream() não foi implantado para esta classe')
    
    def health(self) -> int:
        '''
        Teste simples de verificação se a API está ativa

        Retorna o Status_code da requests.Response resultante da chamada À API
        '''
        raise NotImplementedError('Método health() não foi implantado para esta classe')
        
class ClienteOllama(ClienteLLM):
    # Client implementation for Ollama LLM API
    '''
    Especialização da classe Cliente LLM, a ser utilizada com a API Ollama

    Consultar documentação para detalhes sobre os parâmetros: https://ollama.readthedocs.io/en/modelfile/#valid-parameters-and-values
    '''

    def __init__(self, nome_modelo: str, url_llm: str, temperature: float=configuracoes.temperature, top_k: int=configuracoes.top_k, top_p: float=configuracoes.top_p):
        super().__init__(
            nome_modelo=nome_modelo,
            url_llm=url_llm,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p)
        
        # Nota -- os valores padrão do Ollama são os seguintes:
        #   temperature = 0.8
        #   top_k = 40
        #   top_p = 0.9
        
    def health(self) -> int:
        # Teste simples de verificação se a API está ativa
        '''
        Teste simples de verificação se a API está ativa

        Retorna o Status_code da requests.Response resultante da chamada À API
        '''
        url_llm = f"{self.url_llm}/"
        response_llm = requests.get(url_llm)
        return response_llm.status_code

    async def stream(self, mensagens: List[dict]):
        '''
        Faz requisição POST à API do LLM, enviando um conjunto de mensagens e recebendo a resposta do LLM

        Parâmetros:
            mensagens (List[dict]): lista de mensagens anteriores, bem como a mais recente a serem enviadas à API.
                                    O formato de cada mensagem é: {'role': papel_do_autor_da_mensagem, 'content': conteudo_mensagem},
                                    em que os papéis disponíveis são: 'system', 'user' e 'assistant'.
        Retorna:
            Uma série de str serializáveis em formato JSON com as respostas da API
        '''

        # Envia solicitação ao endpoint de geração de texto usando a opção de 'stream'
        url = f"{self.url_llm}/api/chat"
        
        payload = {
            "model": self.modelo,
            "messages": mensagens,
            "temperature": self.temperature,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "stream": True,
            # "max_new_tokens": 4096 # AFAZER: Considerar remover este atributo
        }
        
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=payload, timeout=120) as resposta:
                resposta.raise_for_status()

                async for fragmento in resposta.aiter_bytes():
                    if fragmento:
                        try:
                            yield json.loads(fragmento.decode())
                        except:
                            print('ERRO: falha na serialização do fragmento\n' + fragmento.decode())

class ClienteOpenAi(ClienteLLM):
    # Client implementation for OpenAI-compatible LLM API
    # AFAZER: Verificar implementação
    '''
    Especialização da classe Cliente LLM, a ser utilizada com a API da OpenAI
    '''
    def __init__(self, nome_modelo: str, url_llm: str, temperature: float=configuracoes.temperature):
        super().__init__(
            nome_modelo=nome_modelo,
            url_llm=url_llm,
            temperature=temperature)

    async def stream(self, mensagens: List[dict]):
        '''
        Faz requisição POST à API do LLM, enviando um conjunto de mensagens e recebendo a resposta do LLM

        Parâmetros:
            mensagens (List[dict]): lista de mensagens anteriores, bem como a mais recente a serem enviadas à API.
                                    O formato de cada mensagem é: {'role': papel_do_autor_da_mensagem, 'content': conteudo_mensagem},
                                    em que os papéis disponíveis são: 'system', 'user' e 'assistant'.
        Retorna:
            Uma série de str serializáveis em formato JSON com as respostas da API
        '''
        url = f"{self.url_llm}/api/chat"
        
        payload = {
            "model": self.modelo,
            "messages": mensagens,
            "temperature": self.temperature,
            "stream": True
        }
        
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=payload, timeout=120) as resposta:
                resposta.raise_for_status()

                async for fragmento in resposta.aiter_bytes():
                    if fragmento:
                        try:
                            yield json.loads(fragmento.decode())
                        except:
                            print('ERROR: Failed to deserialize fragment\n' + fragmento.decode())
    
class InterfaceLLM:
    # Base interface class for LLM interactions
    '''
    Interface base para interações com Clientes de LLMs

    Atributos:
        definicoes_sistema (str): mensagem 'system' utilizada para definir o papel do LLM e orientações gerais
    Métodos:
        health: teste simples de verificação se a API está ativa
        formatar_prompt_usuario: utiliza o template de prompt de usuário no arquivo de configurações para gerar
                                 mensagem formatada.
        formatar_mensagens_chat: utiliza o histórico e o prompt de usuário para gerar dados a serem enviados à API do LLM
        gerar_resposta_llm: invoca o cliente LLM para fazer a requisição à API do LLM por uma resposta
    '''
    
    def __init__(self):
        '''Inicializa interface LLM utilizando configurações definidas no arquivo de configurações'''
        self.definicoes_sistema = configuracoes.template_mensagem_system
        
    def health(self) -> int:
        raise NotImplementedError('Método health() não foi implantado para esta classe')

    def formatar_prompt_usuario(self, pergunta: str, documentos: List[str]) -> str:
        # Creates formatted user prompt to be sent to the LLM API
        '''
        Gera prompt de usuário formatado para envio à API do LLM

        Parâmetros:
            pergunta (str): pergunta feita pelo usuário
            documentos (List[str]): lista de textos a serem utilizados como contexto para geração da resposta

        Retorna:
            (str) Prompt formatado conforme template contido no arquivo de configurações
        '''

        return configuracoes.template_prompt_usuario.format('\n'.join(documentos), pergunta)

    def formatar_mensagens_chat(self, prompt_usuario: str, historico: List[Tuple[str, str]]) -> List[Dict[str, str]]:
        # Formats chat messages with system instructions and history
        '''
        Gera lista de mensagens a ser enviada ao LLM para geração de resposta

        Parâmetros:
            prompt_usuario (str): prompt formatado, gerado com base em documentos e na pergunta do usuário
            histórico (List[Tuple[str, str]]): lista de tuplas representando as interações anteriores. Cada tupla contém o papel e o conteúdo da mensagem.

        Retorna:
            (List[Dict[str, str]]): Uma lista de dicionários, em que cada entrada é uma interação anterior, mais a interação atual.
        '''

        mensagens = [{'role': 'system', 'content': self.definicoes_sistema}]

        for pergunta, resposta in historico:
            mensagens.append({'role': 'user', 'content': pergunta})
            mensagens.append({'role': 'assistant', 'content': resposta})

        mensagens.append({'role': 'user', 'content': prompt_usuario})
        
        return mensagens
    
    async def gerar_resposta_llm(self, pergunta: str, documentos: List[str], historico: List[Tuple[str, str]]):
        raise NotImplementedError('Método gerar_resposta_llm() não foi implantado para esta classe')

class InterfaceOllama(InterfaceLLM):
    # Implementation of the LLM interface using Ollama
    '''
    Especialização da classe InterfaceLLM, para utilização com a API Ollama.

    Atributos:
        cliente_ollama (ClenteOllama): responsável pela comunicação com a API Ollama.

    Métodos:
        health(): teste simples de verificação se a API está ativa
        formatar_prompt_usuario: utiliza o template de prompt de usuário no arquivo de configurações para gerar
                                 mensagem formatada.
        formatar_mensagens_chat: utiliza o histórico e o prompt de usuário para gerar dados a serem enviados à API do LLM
        gerar_resposta_llm: invoca o cliente LLM para fazer a requisição à API do LLM por uma resposta
    '''

    def __init__(self, nome_modelo: str, url_ollama: str, temperature: float=configuracoes.temperature):
        '''Inicializa interface, criando o ClienteLLM'''

        super().__init__()
        self.cliente_ollama = ClienteOllama(url_llm=url_ollama, nome_modelo=nome_modelo, temperature=temperature)
        
    def health(self) -> int:
        '''Teste simples de verificação se a API está ativa'''
        return self.cliente_ollama.health()
        
    async def gerar_resposta_llm(self, pergunta: str, documentos: List[str], historico: List[Tuple[str, str]]):
        '''
        Invoca o ClienteLLM para realizar requisição à API do LLM e retorna resposta em formato de 'stream'

        Parâmetros:
            pergunta (str): pergunta do usuário
            documentos (List[str]): Lista de documentos a ser utilizada como contexto pelo LLM para responder a pergunta
            historico (List[Tuple[str, str]]): lista de tuplas representando as interações anteriores. Cada tupla contém o papel e o conteúdo da mensagem

        Retorna:
            Uma série de str serializáveis em formato JSON com as respostas da API
        '''

        prompt_usuario = self.formatar_prompt_usuario(pergunta, documentos)
        mensagens = self.formatar_mensagens_chat(prompt_usuario=prompt_usuario, historico=historico)
        async for fragmento_resposta in self.cliente_ollama.stream(mensagens=mensagens):
            yield fragmento_resposta

class InterfaceChroma:
    # Interface for interacting with a ChromaDB-based vector database
    '''
    Interface para interação com o banco vetorial baseado no ChromaDB

    Atributos:
        banco_de_vetores (chromadb.PersistentClient): Cliente ChromaDB com persistência
        colecao_documentos (chromadb.Collection): coleção de documentos com embeddings, para realização de consultas
    '''
    def __init__(self,
                 url_banco_vetores=configuracoes.url_banco_vetores,
                 colecao_de_documentos=configuracoes.nome_colecao_de_documentos,
                 funcao_de_embeddings=None,
                 fazer_log=True):
    
        if fazer_log: print('--- interface do ChromaDB em inicialização')

        if not funcao_de_embeddings:
            if fazer_log: print(f'--- criando a função de embeddings do ChromaDB com {configuracoes.modelo_funcao_de_embeddings} (device={configuracoes.device})...')
            funcao_de_embeddings = FuncaoEmbeddings(model_name=configuracoes.modelo_funcao_de_embeddings, biblioteca=SentenceTransformer, device=configuracoes.device)
        
        if fazer_log: print(f'--- inicializando banco de vetores (usando "{url_banco_vetores}")...')
        self.banco_de_vetores = chromadb.PersistentClient(path=url_banco_vetores)

        if fazer_log: print(f'--- definindo a coleção a ser usada ({colecao_de_documentos})...')
        self.colecao_documentos = self.banco_de_vetores.get_collection(name=colecao_de_documentos, embedding_function=funcao_de_embeddings)
    
    def consultar_documentos(self, termos_de_consulta: str, num_resultados=configuracoes.num_documentos_retornados) -> chromadb.QueryResult:
        return self.colecao_documentos.query(query_texts=[termos_de_consulta], n_results=num_resultados)

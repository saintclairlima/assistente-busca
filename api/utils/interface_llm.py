import requests
from pydantic import BaseModel

import httpx
import json
from api.configuracoes.config_gerais import configuracoes
from typing import Dict, List, Optional, Tuple

# Data model for chat interactions
class DadosChat(BaseModel):
    '''
    Classe que modela uma interação com o chat

    Atributos:
        pergunta (str): pergunta do usuário
        historico (List[str]): histórico com as últimas interações
        id_sessao (str): identificador da sessão, servindo para agrupar interações por sessão
        id_cliente(str): identificador do cliente inicializador da sessão
        intencao(str): identificador da intenção da pergunta, atribuída por um classificador
    '''

    pergunta: str
    historico: list
    id_sessao: str
    id_cliente: str
    intencao: Optional[str] = None

class ClienteLLM:
    # Base client class for LLM interactions
    '''
    Classe base a ser utilizada em interações com um LLM em uma API

    Atributos:
        modelo (str): nome do modelo a ser utilizado
        url_llm (str): url onde a API do LLM se encontra
        temperature (float): temperatura do modelo. Valores altos fazem o modelo responder de forma mais criativa
        top_k (int): Reduz a probabilidade de gerar alucinação. Valores altos (ex. 100) resultam em respostas com diversidade; valores baixos (ex. 10) são mais conservadores
        top_p (float): Atua junto com top_k. Valores altos (ex. 0.95) resultam em texto mais diverso; valores baixos (ex. 0.5) geram texto mais conservador e focado.

    Métodos:
        health(): teste simples de verificação se a API está ativa
        stream(mensagens: List[dict]): Envia solicitação ao endpoint de geração de texto usando a opção de 'stream' (obtendo a resposta em framentos)
    '''

    def __init__(self, nome_modelo: str, url_llm: str, temperature: float=configuracoes.temperature, top_k: int=configuracoes.top_k, top_p: float=configuracoes.top_p, usar_raciocinio: bool=configuracoes.usar_raciocinio):

        self.modelo = nome_modelo
        self.url_llm = url_llm
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.usar_raciocinio = usar_raciocinio
    
    async def gerar_resposta_stream(self, mensagens: List[dict]):
        raise NotImplementedError('Método stream() não foi implantado para esta classe')
    
    def health(self) -> int:
        '''
        Teste simples de verificação se a API está ativa

        Retorna o Status_code da requests.Response resultante da chamada À API
        '''
        raise NotImplementedError('Método health() não foi implantado para esta classe')

    def gerar_embeddings(self, texto: str):
        '''
        Utiliza o modelo do cliente para gerar embeddings do texto fornecido

        Parâmetros:
            texto (str): texto a ser convertido em embeddings.
            
        Retorna:
            Uma série de str serializáveis em formato JSON com as respostas da API
        '''
        raise NotImplementedError('Método health() não foi implantado para esta classe')
        
class ClienteOllama(ClienteLLM):
    # Client implementation for Ollama LLM API
    '''
    Especialização da classe Cliente LLM, a ser utilizada com a API Ollama

    Consultar documentação para detalhes sobre os parâmetros: https://ollama.readthedocs.io/en/modelfile/#valid-parameters-and-values
    '''

    def __init__(self, nome_modelo: str, url_llm: str, temperature: float=configuracoes.temperature, top_k: int=configuracoes.top_k, top_p: float=configuracoes.top_p, usar_raciocinio: bool=configuracoes.usar_raciocinio):
        super().__init__(
            nome_modelo=nome_modelo,
            url_llm=url_llm,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            usar_raciocinio=usar_raciocinio)
        
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

    async def gerar_resposta_stream(self, mensagens: List[dict]):
        '''
        Faz requisição POST à API do LLM, enviando um conjunto de mensagens e recebendo a resposta do LLM por stream (token a token)

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
            "think": self.usar_raciocinio,
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
    
    async def gerar_resposta(self, mensagens: List[dict]):
        '''
        Faz requisição POST à API do LLM, enviando um conjunto de mensagens e recebendo a resposta do LLM de uma só vez

        Parâmetros:
            mensagens (List[dict]): lista de mensagens anteriores, bem como a mais recente a serem enviadas à API.
                                    O formato de cada mensagem é: {'role': papel_do_autor_da_mensagem, 'content': conteudo_mensagem},
                                    em que os papéis disponíveis são: 'system', 'user' e 'assistant'.
        Retorna:
            Uma str serializável em formato JSON com a resposta completa da API
        '''

        # Envia solicitação ao endpoint de geração de texto sem utilizar stream
        url = f"{self.url_llm}/api/chat"        
        payload = {
            "model": self.modelo,
            "messages": mensagens,
            "temperature": self.temperature,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "think": self.usar_raciocinio,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def gerar_resposta_llm_json(self, mensagens: List[dict], formato:dict) -> str:
        '''
        Faz requisição POST à API do LLM, enviando um conjunto de mensagens e recebendo a resposta do LLM de uma só vez, estruturada em formato JSON

        Parâmetros:
            mensagens (List[dict]): lista de mensagens anteriores, bem como a mais recente a serem enviadas à API.
                                    O formato de cada mensagem é: {'role': papel_do_autor_da_mensagem, 'content': conteudo_mensagem},
                                    em que os papéis disponíveis são: 'system', 'user' e 'assistant'.
            formato (dict): dicionário com o formato de retorno esperado para a resposta. Os campos são:
                            'type': deve ter o valor 'object';
                            'properties': dicionário em que cada entrada é a descrição de uma propriedade
                                          que a resposta deve conter. É um dicionário em que as chaves são os nomes das propriedades;
                            'required': uma lista com os nomes das propriedades que são obrigatórias na resposta.
                            EX: {
                                "type": "object",
                                "properties": {
                                    "propriedade1": {
                                        "type": "string",
                                    },
                                    "propriedade2": {
                                        "type": "float"
                                    },
                                    "propriedade3": {
                                        "type": "array",
                                        "items": {
                                            "type": "string"
                                        }
                                    }
                                }
                            }
        Retorna:
            Uma str serializável em formato JSON com a resposta completa da API
        '''

        # Envia solicitação ao endpoint de geração de texto utilizando o formato especificado de resposta
        url = f"{self.url_llm}/api/chat"        
        payload = {
            "model": self.modelo,
            "messages": mensagens,
            "format": formato,
            "temperature": 0.0,
            "top_k": 0,
            "top_p": 0,
            "think": self.usar_raciocinio,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    def gerar_embeddings(self, texto: str):
        url_llm = f"{self.url_llm}/api/embed"
        data = {
            "model": self.modelo,
            "input": texto
        }

        resposta = requests.post(url_llm, json=data)
        embeddings = json.loads(resposta.content)['embeddings']
        return embeddings

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

    async def gerar_resposta_stream(self, mensagens: List[dict]):
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
        gerar_resposta_llm_stream: invoca o cliente LLM para fazer a requisição à API do LLM por uma resposta
    '''
    
    def __init__(self, definicoes_sistema: str=configuracoes.template_mensagem_system):
        '''Inicializa interface LLM utilizando configurações definidas no arquivo de configurações'''
        self.definicoes_sistema = definicoes_sistema
        
    def health(self) -> int:
        raise NotImplementedError('Método health() não foi implantado para esta classe')

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
    
    async def gerar_resposta_llm_stream(self, prompt_usuario: str, historico: List[Tuple[str, str]]):
        raise NotImplementedError('Método gerar_resposta_llm_stream() não foi implantado para esta classe')
    
    async def gerar_resposta_llm(self, prompt_usuario: str, historico: List[Tuple[str, str]]):
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
        gerar_resposta_llm_stream: invoca o cliente LLM para fazer a requisição à API do LLM por uma resposta
    '''

    def __init__(self,
                 nome_modelo: str,
                 url_ollama: str,
                 definicoes_sistema: str=configuracoes.template_mensagem_system,
                 temperature: float=configuracoes.temperature,
                 top_k: float=configuracoes.top_k,
                 top_p: float=configuracoes.top_p):
        
        '''Inicializa interface, criando o ClienteLLM'''

        super().__init__(definicoes_sistema=definicoes_sistema)
        self.cliente_ollama = ClienteOllama(url_llm=url_ollama, nome_modelo=nome_modelo, temperature=temperature, top_k=top_k, top_p=top_p)
        
    def health(self) -> int:
        '''Teste simples de verificação se a API está ativa'''
        return self.cliente_ollama.health()
        
    async def gerar_resposta_llm_stream(self, prompt_usuario: str, historico: List[Tuple[str, str]]):
        '''
        Invoca o ClienteLLM para realizar requisição à API do LLM e retorna resposta em formato de 'stream'

        Parâmetros:
            prompt_usuario (str): prompt do usuário
            historico (List[Tuple[str, str]]): lista de tuplas representando as interações anteriores. Cada tupla contém o papel e o conteúdo da mensagem

        Retorna:
            Uma série de str serializáveis em formato JSON com as respostas da API
        '''

        # AFAZER Ajeitar esse método aqui
        mensagens = self.formatar_mensagens_chat(prompt_usuario=prompt_usuario, historico=historico)
        async for fragmento_resposta in self.cliente_ollama.gerar_resposta_stream(mensagens=mensagens):
            yield fragmento_resposta
        
    async def gerar_resposta_llm(self, prompt_usuario: str, historico: List[Tuple[str, str]]):
        '''
        Invoca o ClienteLLM para realizar requisição à API do LLM e retorna resposta em formato de 'stream'

        Parâmetros:
            prompt_usuario (str): prompt do usuário
            historico (List[Tuple[str, str]]): lista de tuplas representando as interações anteriores. Cada tupla contém o papel e o conteúdo da mensagem

        Retorna:
            Uma série de str serializáveis em formato JSON com as respostas da API
        '''
        
        mensagens = self.formatar_mensagens_chat(prompt_usuario=prompt_usuario, historico=historico)
        return self.cliente_ollama.gerar_resposta(mensagens=mensagens)

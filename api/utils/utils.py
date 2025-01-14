from chromadb import chromadb, Documents, EmbeddingFunction, Embeddings
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from torch import cuda

import httpx
import json
from api.environment.environment import environment
from typing import List, Tuple


class DadosChat(BaseModel):
    pergunta: str
    historico: list

class FuncaoEmbeddings(EmbeddingFunction):
    # A instrução oferecida tem melhor resultado em inglês e no formato proposto no artigo do instructor. (Represent the legislative document question for retrieving supporting documents)
    def __init__(self, nome_modelo: str, tipo_modelo=SentenceTransformer, device: str=None, instrucao: str="Represent the legislative document for retrieval:"):
        if device:
            self.device = device
        else:
            self.device = 'cuda' if cuda.is_available() else 'cpu'

        # Carrega o modelo pre-treinado a partir do tipo de modelo escolhido
        self.model = tipo_modelo(nome_modelo, device=self.device)
        self.model.to(self.device)
        self.instrucao = instrucao

    def __call__(self, input: Documents) -> Embeddings:
        # obtém os embeddings do texto
        if self.instrucao:
            input_instrucao = [(self.instrucao, doc) for doc in input]
            embeddings = self.model.encode(input_instrucao, convert_to_numpy=True, device=self.device)
        else:
            embeddings = self.model.encode(input, convert_to_numpy=True, device=self.device)
        return embeddings.tolist()
    
class ClienteLLM:
    def __init__(self, nome_modelo: str, url_llm: str, temperature: float=0):
        self.modelo = nome_modelo
        self.url_llm = url_llm
        self.temperature = temperature
    
    async def stream(self, mensagens: List[dict]):
        raise NotImplementedError('Método stream() não foi implantado para esta classe')
        
    
class ClienteOllama(ClienteLLM):
    def __init__(self, nome_modelo: str, url_llm: str, temperature: float=0):
        super().__init__(
            nome_modelo=nome_modelo,
            url_llm=url_llm,
            temperature=temperature)

    async def stream(self, mensagens: List[dict]):
        url = f"{self.url_llm}/api/chat"
        
        payload = {
            "model": self.modelo,
            "messages": mensagens,
            "temperature": self.temperature,
            "stream": True,
            # "max_new_tokens": 4096 ## AFAZER: considerar remover esse atributo
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

class InterfaceLLM:
    
    def __init__(self):
        self.papel_do_LLM = '''ALERN e ALRN significam Assembleia Legislativa do Estado do Rio Grande do Norte.
Você é um assistente que responde a dúvidas de servidores da ALERN sobre o regimento interno da ALRN, o regime jurídico dos servidores estaduais do RN, bem como resoluções da ALRN.
Assuma um tom formal, porém caloroso, com gentileza nas respostas. Utilize palavras e termos que sejam claros, autoexplicativos e linguagem simples, próximo do que o cidadão comum utiliza.'''
        self.diretrizes = '''Use as informações dos DOCUMENTOS fornecidos para gerar uma resposta clara para a PERGUNTA.
Na resposta, não mencione que foi fornecido documentos de referência. Cite os nomes dos DOCUMENTOS e números dos artigos em que a resposta se baseia.
A resposta não deve ter saudação, vocativo, nem qualquer tipo de introdução que dê a entender que não houve interação anterior.
Se você não souber a resposta, assuma um tom gentil e diga que não tem informações suficientes para responder.'''

    def formatar_prompt_usuario(self, pergunta: str, documentos: List[str]):
        return 'DOCUMENTOS:\n{}\nPERGUNTA: {}'.format('\n'.join(documentos), pergunta)

    def formatar_mensagens_chat(self, prompt_usuario: str, historico:List[Tuple[str, str]]):
        definicoes_sistema = f'''PAPEL: {self.papel_do_LLM}. DIRETRIZES PARA AS RESPOSTAS: {self.diretrizes}'''

        mensagens = [{'role': 'system', 'content': definicoes_sistema}]

        for pergunta, resposta in historico:
            mensagens.append({'role': 'user', 'content': pergunta})
            mensagens.append({'role': 'assistant', 'content': resposta})

        mensagens.append({'role': 'user', 'content': prompt_usuario})
        
        return mensagens
    
    async def gerar_resposta_llm(self, pergunta: str, documentos: List[str], historico:List[Tuple[str, str]]):
        raise NotImplementedError('Método gerar_resposta_llm() não foi implantado para esta classe')
        
class InterfaceOllama(InterfaceLLM):
    def __init__(self, nome_modelo: str, url_ollama: str, temperature: float=0):
        super().__init__()
        self.cliente_ollama = ClienteOllama(url_llm=url_ollama, nome_modelo=nome_modelo, temperature=temperature)
        
    async def gerar_resposta_llm(self, pergunta: str, documentos: List[str], historico:List[Tuple[str, str]]):
        prompt_usuario = self.formatar_prompt_usuario(pergunta, documentos)
        mensagens = self.formatar_mensagens_chat(prompt_usuario=prompt_usuario, historico=historico)
        async for fragmento_resposta in self.cliente_ollama.stream(mensagens=mensagens):
            yield fragmento_resposta

class InterfaceChroma:
    def __init__(self,
                 url_banco_vetores=environment.URL_BANCO_VETORES,
                 colecao_de_documentos=environment.NOME_COLECAO_DE_DOCUMENTOS,
                 funcao_de_embeddings=None,
                 fazer_log=True):
    
        if fazer_log: print('--- interface do ChromaDB em inicialização')

        if not funcao_de_embeddings:
            print(f'--- criando a função de embeddings do ChromaDB com {environment.MODELO_DE_EMBEDDINGS} (device={environment.DEVICE})...')
            funcao_de_embeddings = FuncaoEmbeddings(model_name=environment.MODELO_DE_EMBEDDINGS, biblioteca=SentenceTransformer, device=environment.DEVICE)
        
        if fazer_log: print(f'--- inicializando banco de vetores (usando "{url_banco_vetores}")...')
        self.banco_de_vetores = chromadb.PersistentClient(path=url_banco_vetores)

        if fazer_log: print(f'--- definindo a coleção a ser usada ({colecao_de_documentos})...')
        self.colecao_documentos = self.banco_de_vetores.get_collection(name=colecao_de_documentos, embedding_function=funcao_de_embeddings)
    
    def consultar_documentos(self, termos_de_consulta: str, num_resultados=environment.NUM_DOCUMENTOS_RETORNADOS):
        return self.colecao_documentos.query(query_texts=[termos_de_consulta], n_results=num_resultados)
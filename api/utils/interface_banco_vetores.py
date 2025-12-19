from typing import Callable
from chromadb import chromadb, Documents, EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer
from torch import cuda
from api.utils.interface_llm import ClienteOllama
from api.configuracoes.config_gerais import configuracoes



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
    
class FuncaoEmbeddingsAPI(EmbeddingFunction):
    # Custom embedding function using API calls
    '''
    Função de embeddings customizada, a ser utilizada com chamadas a APIs

    Atributos:
        url_api (str): url onde se localiza a API geradora de embeddings
        nome_modelo (str): nome do modelo utilizado
    '''

    def __init__(self, url_api: str, nome_modelo: str):
        '''
        Inicializa a função

        Parâmetros:
            url_api (str): url onde se localiza a API geradora de embeddings
            nome_modelo (str): nome do modelo utilizado
        '''

        # Carrega modelo pré-treinado com remote code trust habilitado
        self.url_api = url_api
        self.nome_modelo = nome_modelo

    def __call__(self, input: Documents) -> Embeddings:
        '''
        Gera embeddings para uma coleção de documentos

        Parâmetros:
            input (chromadb.Documents): uma lista de strings com o conteúdo a ser representado por embeddings
        
        Retorna:
            (chroma.Embeddings): uma lista de representações de Embeddings (List[ndarray[Any, dtype[signedinteger[_32Bit] | floating[_32Bit]]]])
        '''
        raise NotImplementedError('Método consultar_documentos() não foi implantado para esta classe')

class FuncaoEmbeddingsOllama(FuncaoEmbeddingsAPI):
    '''
    Especialização de FuncaoEmbeddingsAPI voltada para uso com o Ollama
    '''

    def __init__(self, url_api, nome_modelo):
        super().__init__(url_api, nome_modelo)
    
    def __call__(self, input: Documents) -> Embeddings:
        llm = ClienteOllama(nome_modelo=self.nome_modelo, url_llm=self.url_api)
        embeddings = llm.gerar_embeddings(input)
        return embeddings
    
class FuncaoEmbeddingsGeneric(EmbeddingFunction):
    '''
    Oferece uma possibilidade de função de embedding completamente customizada

    Atributos:
        funcao (Callable[[Documents], Embeddings]): função a ser utilizada para gerar os embeddings
    '''

    def __init__(self, funcao: Callable[[Documents], Embeddings]):
        '''
        Inicializa a função

        Parâmetros:
            funcao (Callable[[Documents], Embeddings]): função a ser utilizada para gerar os embeddings
        '''
        
        self.funcao = funcao

    def __call__(self, input: Documents) -> Embeddings:
        '''
        Gera embeddings para uma coleção de documentos

        Parâmetros:
            input (chromadb.Documents): uma lista de strings com o conteúdo a ser representado por embeddings
        
        Retorna:
            (chroma.Embeddings): uma lista de representações de Embeddings (List[ndarray[Any, dtype[signedinteger[_32Bit] | floating[_32Bit]]]])
        '''
        return self.funcao(input)
        
    
class InterfaceBancoVetorial:
    # Base class for interfacing with vector stores
    '''
    Classe base a ser utilizada em interações vector stores/bancos vetoriais
    '''

    def consultar_documentos(self, termos_de_consulta: str, num_resultados=configuracoes.num_documentos_retornados) -> chromadb.QueryResult:
        raise NotImplementedError('Método consultar_documentos() não foi implantado para esta classe') 

class InterfaceChroma(InterfaceBancoVetorial):
    # Interface for interacting with a ChromaDB-based vector database
    '''
    Especialização de InterfaceBancoVetorial, voltada para interação com o banco vetorial baseado no ChromaDB

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
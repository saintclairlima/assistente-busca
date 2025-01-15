import json

class ConfiguracoesAplicacao:
    def __init__(self):
        self.URL_INDICE_DOCUMENTOS='api/dados/documentos/index.json'
        
        with open(self.URL_INDICE_DOCUMENTOS, 'r') as arq:
            self.documentos = json.load(arq)
            
        self.threadpool_max_workers=10
        
        self.url_banco_vetores = 'api/dados/bancos_vetores/banco_assistente'
        self.nome_colecao_de_documentos = 'documentos_rh'
        self.embedding_instructor = 'hkunlp/instructor-xl'
        self.embedding_squad_portuguese = 'pierreguillou/bert-base-cased-squad-v1.1-portuguese'
        self.num_documentos_retornados = 5

        self.modelo_funcao_de_embeddings = self.embedding_instructor

        self.cliente_llm = 'ollama'
        self.modelo_llm = 'llama3.1'
        self.temperature = 0
        self.top_k = 0
        self.top_p = 0
        
    def configuracoes_banco_vetores(self):
        return {
            'url_banco_vetores': self.url_banco_vetores,
            'nome_colecao_de_documentos': self.nome_colecao_de_documentos,
            'num_documentos_retornados': self.num_documentos_retornados,
            'modelo_funcao_de_embeddings': self.modelo_funcao_de_embeddings
        }
        
    def configuracoes_llm(self):
        return {
            'cliente_llm': self.cliente_llm,
            'modelo_llm': self.modelo_llm,
            'temperature': self.temperature,
            'top_k': self.top_k,
            'top_p': self.top_p
        }
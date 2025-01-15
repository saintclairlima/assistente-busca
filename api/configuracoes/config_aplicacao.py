
import json


class ConfiguracoesAplicacao:
    def __init__(self):
        self.URL_INDICE_DOCUMENTOS='api/dados/documentos/index.json'
        
        with open(self.URL_INDICE_DOCUMENTOS, 'r') as arq:
            self.documentos = json.load(arq)
            
        self.threadpool_max_workers=10
        
        self.url_banco_vetores = 'api/dados/bancos_vetores/resultados_testes'
        self.nome_colecao_de_documentos='sem_instrucao'
        self.embedding_instructor='hkunlp/instructor-xl'
        self.embedding_squad_portuguese='pierreguillou/bert-base-cased-squad-v1.1-portuguese'
        self.num_documentos_retornados=5

        self.modelo_funcao_de_embeddings = self.embedding_instructor

        self.cliente_llm='ollama'
        self.modelo_llm='llama3.1'
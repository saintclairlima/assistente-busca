import json
import os

class ConfiguracoesAplicacao:
    def __init__(self):
        self.url_indice_documentos='api/dados/documentos/index.json'
        with open(self.url_indice_documentos, 'r') as arq:
            self.documentos = json.load(arq)

        with open('api/configuracoes/mensagens.json', 'r', encoding='utf-8') as arq:
            self.mensagens=json.load(arq)
            
        self.threadpool_max_workers=10
        
        self.url_pasta_documentos = os.path.normpath('api/dados/documentos')
        self.url_banco_vetores = os.path.normpath('api/dados/bancos_vetores/banco_assistente')
        self.nome_colecao_de_documentos = 'documentos_rh'
        self.num_maximo_palavras_por_fragmento = 300
        self.hnsw_space = 'cosine' # métrica a ser utilizada pelo banco vetorial para medir similaridade de vetores
        self.embedding_instructor = 'hkunlp/instructor-xl'
        self.embedding_squad_portuguese = 'pierreguillou/bert-base-cased-squad-v1.1-portuguese'
        self.embedding_alibaba_gte = 'Alibaba-NLP/gte-multilingual-base'
        self.embedding_openai = 'text-embedding-ada-002'
        self.url_cache_modelos = '/var/modelos_ia/cache'
        os.environ['HF_HOME'] = self.url_cache_modelos
        os.environ['TRANSFORMERS_CACHE'] = self.url_cache_modelos 
        self.num_documentos_retornados = 5
        
        self.url_script_geracao_banco_sqlite=os.path.normpath('api/dados/scripts_geracao_sqlite.sql')
        self.url_script_geracao_banco_sql=os.path.normpath('api/dados/scripts_geracao.sql')

        self.modelo_funcao_de_embeddings = self.embedding_instructor
        
        self.cliente_llm = 'ollama'
        self.modelo_llm = 'llama3.1'
        self.temperature = 0
        self.top_k = 0
        self.top_p = 0

        self.papel_llm = self.mensagens['papel_llm']
        self.diretrizes_llm = self.mensagens['diretrizes_llm']
        self.template_mensagem_system = f'''PAPEL: {self.papel_llm}. DIRETRIZES PARA AS RESPOSTAS: {self.diretrizes_llm}'''
        self.template_prompt_usuario = 'DOCUMENTOS:\n{}\nPERGUNTA: {}'

        self.mensagens_retorno = self.mensagens['mensagens_retorno']
        
    def configuracoes_banco_vetores(self):
        return {
            'url_banco_vetores': self.url_banco_vetores,
            'nome_colecao_de_documentos': self.nome_colecao_de_documentos,
            'num_documentos_retornados': self.num_documentos_retornados,
            'modelo_funcao_de_embeddings': self.modelo_funcao_de_embeddings,
            'hnsw_space': self.hnsw_space
        }
        
    def configuracoes_llm(self):
        return {
            'cliente_llm': self.cliente_llm,
            'modelo_llm': self.modelo_llm,
            'temperature': self.temperature,
            'top_k': self.top_k,
            'top_p': self.top_p,
            'template_mensagem_system': self.template_mensagem_system,
            'template_prompt_usuario': self.template_prompt_usuario
        }
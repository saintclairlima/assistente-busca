import json
import os

class ConfiguracoesAplicacao:
    def __init__(self):

        with open('api/configuracoes/arq_conf.json', 'r', encoding='utf-8') as arq:
            configs = json.load(arq)

        url_indice_documentos=configs['url_indice_documentos']
        with open(url_indice_documentos, 'r', encoding='utf-8') as arq:
            self.documentos = json.load(arq)

        with open(configs['url_arquivo_mensagens'], 'r', encoding='utf-8') as arq:
            mensagens = json.load(arq)
            
        self.threadpool_max_workers=configs['threadpool_max_workers']
        
        self.url_pasta_documentos = os.path.normpath(configs['url_pasta_documentos'])
        self.url_pasta_bancos_vetores = os.path.normpath(configs['url_pasta_bancos_vetores'])
        self.url_banco_vetores = os.path.normpath(configs['url_banco_vetores'])
        self.nome_colecao_de_documentos = configs['nome_colecao_de_documentos']
        self.num_maximo_palavras_por_fragmento = configs['num_maximo_palavras_por_fragmento']
        self.hnsw_space = configs['hnsw_space'] # métrica a ser utilizada pelo banco vetorial para medir similaridade de vetores
        self.embedding_instructor = configs['embedding_instructor']
        self.embedding_squad_portuguese = configs['embedding_squad_portuguese']
        self.embedding_alibaba_gte = configs['embedding_alibaba_gte']
        self.embedding_openai = configs['embedding_openai']
        self.embedding_llama = configs['embedding_llama']
        self.embedding_deepseek = configs['embedding_deepseek']
        self.embedding_bge_m3 = configs['embedding_bge_m3']
        self.url_cache_modelos = os.path.abspath(configs['url_cache_modelos'])
        os.environ['HF_HOME'] = self.url_cache_modelos
        os.environ['HF_HUB_CACHE'] = self.url_cache_modelos
        os.environ['HF_ASSETS_CACHE'] = self.url_cache_modelos
        os.environ['TRANSFORMERS_CACHE'] = self.url_cache_modelos

        self.num_documentos_retornados = configs['num_documentos_retornados']
        
        self.url_script_geracao_banco_sqlite=os.path.normpath(configs['url_script_geracao_banco_sqlite'])
        self.url_script_geracao_banco_sql=os.path.normpath(configs['url_script_geracao_banco_sql'])

        self.modelo_funcao_de_embeddings = configs['modelo_funcao_de_embeddings']
        
        self.cliente_llm = configs['cliente_llm']
        self.modelo_llm = configs['modelo_llm']
        self.temperature = configs['temperature']
        self.top_k =configs['top_k']
        self.top_p = configs['top_p']
        self.usar_raciocinio = configs['usar_raciocinio']

        self.papel_llm = mensagens['papel_llm']
        # self.diretrizes_llm = mensagens['diretrizes_llm']
        self.template_mensagem_system = f'''PAPEL: {self.papel_llm}'''
        self.templates_intencoes = mensagens['templates_intencoes']
        self.template_prompt_rag = 'DOCUMENTOS:\n{}\nPERGUNTA: {}'

        self.mensagens_retorno = mensagens['mensagens_retorno']
        self.mensagens_interacao_inadequada = mensagens['mensagens_interacao_inadequada']
        self.mensagem_interacao_documento = mensagens['mensagem_interacao_documento']

        self.permitir_comentarios = configs['permitir_comentarios']
        
    def configuracoes_banco_vetores(self):
        return {
            'url_pasta_bancos_vetores': self.url_pasta_bancos_vetores,
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
            'template_prompt_usuario': self.template_prompt_rag
        }
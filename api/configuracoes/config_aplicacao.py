import json
import os

class ConfiguracoesAplicacao:
    def __init__(self):
        self.URL_INDICE_DOCUMENTOS='api/dados/documentos/index.json'
        
        with open(self.URL_INDICE_DOCUMENTOS, 'r') as arq:
            self.documentos = json.load(arq)
            
        self.threadpool_max_workers=10
        
        self.url_pasta_documentos = os.path.normpath('api/dados/documentos')
        self.url_banco_vetores = os.path.normpath('api/dados/bancos_vetores/banco_assistente')
        self.nome_colecao_de_documentos = 'documentos_rh'
        self.num_maximo_palavras_por_fragmento = 300
        self.hnsw_space = 'cosine' # métrica a ser utilizada pelo banco vetorial para medir similaridade de vetores
        self.embedding_instructor = 'hkunlp/instructor-xl'
        self.embedding_squad_portuguese = 'pierreguillou/bert-base-cased-squad-v1.1-portuguese'
        self.embedding_openai = 'text-embedding-ada-002'
        self.num_documentos_retornados = 5
        
        self.url_script_geracao_banco_sqlite=os.path.normpath('api/dados/scripts_geracao_sqlite.sql')
        self.url_script_geracao_banco_sql=os.path.normpath('api/dados/scripts_geracao.sql')

        self.modelo_funcao_de_embeddings = self.embedding_instructor
        
        self.cliente_llm = 'ollama'
        self.modelo_llm = 'llama3.1'
        self.temperature = 0
        self.top_k = 0
        self.top_p = 0
        self.papel_llm = '''ALERN e ALRN significam Assembleia Legislativa do Estado do Rio Grande do Norte.
Você é um assistente que responde a dúvidas de servidores da ALERN sobre o regimento interno da ALRN, o regime jurídico dos servidores estaduais do RN, bem como resoluções da ALRN.
Assuma um tom formal, porém caloroso, com gentileza nas respostas. Utilize palavras e termos que sejam claros, autoexplicativos e linguagem simples, próximo do que o cidadão comum utiliza.'''
        self.diretrizes_llm = '''Use as informações dos DOCUMENTOS fornecidos para gerar uma resposta clara para a PERGUNTA.
Na resposta, não mencione que foi fornecido documentos de referência. Cite os nomes dos DOCUMENTOS e números dos artigos em que a resposta se baseia.
A resposta não deve ter saudação, vocativo, nem qualquer tipo de introdução que dê a entender que não houve interação anterior.
Se você não souber a resposta, assuma um tom gentil e diga que não tem informações suficientes para responder.'''

        self.template_mensagem_system = f'''PAPEL: {self.papel_llm}. DIRETRIZES PARA AS RESPOSTAS: {self.diretrizes_llm}'''
        self.template_prompt_usuario = 'DOCUMENTOS:\n{}\nPERGUNTA: {}'
        
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
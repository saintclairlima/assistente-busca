import json
import os
from dotenv import load_dotenv

url_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
url_dotenv = os.path.join(url_raiz_projeto, ".env")
load_dotenv(url_dotenv)

class Environment:
    def __init__(self):
        self.url_banco_vetores = os.getenv('URL_BANCO_VETORES')
        self.url_llm=os.getenv('URL_LLM')
        self.url_host=os.getenv('URL_HOST')
        self.tags_substituicao_html={
            'TAG_INSERCAO_URL_HOST': self.url_host
            }

        self.threadpool_max_workers=int(os.getenv('THREADPOOL_MAX_WORKERS'))
        self.nome_colecao_de_documentos=os.getenv('COLECAO_DE_DOCUMENTOS')
        self.embedding_instructor=os.getenv('EMBEDDING_INSTRUCTOR')
        self.embedding_squad_portuguese=os.getenv('EMBEDDING_SQUAD_PORTUGUESE')
        self.cliente_llm=os.getenv('CLIENTE_LLM')
        self.modelo_llm=os.getenv('MODELO_LLM')
        self.device=os.getenv('DEVICE') # ['cpu', cuda']
        self.num_documentos_retornados=int(os.getenv('NUM_DOCUMENTOS_RETORNADOS'))
        self.ambiente_execucao=os.getenv('AMBIENTE_EXECUCAO')
        self.usar_wandb=bool(int(os.getenv('USAR_WANDB')))

        self.modelo_funcao_de_embeddings = self.embedding_instructor
        
        with open(os.getenv('URL_INDICE_DOCUMENTOS'), 'r') as arq:
            self.DOCUMENTOS = json.load(arq)

        # Elementos Wandb
        self.wandb_prefixo='cleiane-projetos' # grumpyai
        self.wandb_nome_projeto="assistente-busca"
        self.wandb_tipo_execucao="producao"

        self.CONFIGS={
            'modelo_funcao_de_embeddings': self.modelo_funcao_de_embeddings,
            'banco_vetorial':{
                'url': self.url_banco_vetores,
                'colecao': self.nome_colecao_de_documentos
            },
            'num_documentos_retornados': self.num_documentos_retornados,
            'threadpool_max_workers': self.threadpool_max_workers,
            'device_api': self.device,
            'ambiente_execucao':self.ambiente_execucao,
            'cliente_llm': self.cliente_llm,
            'modelo_llm': self.modelo_llm,
        }

        self.WANDB_ARTEFATO_BANCO_VETORIAL=f"{self.wandb_prefixo}/{self.wandb_nome_projeto}/banco-vetorial-chroma:latest",
        #AFAZER: colocar artefato do prompt

configuracoes = Environment()
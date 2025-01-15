import json
import os
from dotenv import load_dotenv

url_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
url_dotenv = os.path.join(url_raiz_projeto, ".env")
load_dotenv(url_dotenv)

class Environment:
    def __init__(self):
        self.URL_BANCO_VETORES = os.getenv('URL_BANCO_VETORES')
        self.URL_LLM=os.getenv('URL_LLM')
        self.URL_HOST=os.getenv('URL_HOST')
        self.TAGS_SUBSTITUICAO_HTML={
            'TAG_INSERCAO_URL_HOST': self.URL_HOST
            }

        self.THREADPOOL_MAX_WORKERS=int(os.getenv('THREADPOOL_MAX_WORKERS'))
        self.NOME_COLECAO_DE_DOCUMENTOS=os.getenv('COLECAO_DE_DOCUMENTOS')
        self.EMBEDDING_INSTRUCTOR=os.getenv('EMBEDDING_INSTRUCTOR')
        self.EMBEDDING_SQUAD_PORTUGUESE=os.getenv('EMBEDDING_SQUAD_PORTUGUESE')
        self.CLIENTE_LLM=os.getenv('CLIENTE_LLM')
        self.MODELO_LLM=os.getenv('MODELO_LLM')
        self.DEVICE=os.getenv('DEVICE') # ['cpu', cuda']
        self.NUM_DOCUMENTOS_RETORNADOS=int(os.getenv('NUM_DOCUMENTOS_RETORNADOS'))
        self.AMBIENTE_EXECUCAO=os.getenv('AMBIENTE_EXECUCAO')
        self.USAR_WANDB=bool(int(os.getenv('USAR_WANDB')))

        self.MODELO_FUNCAO_DE_EMBEDDINGS = self.EMBEDDING_INSTRUCTOR
        
        with open(os.getenv('URL_INDICE_DOCUMENTOS'), 'r') as arq:
            self.DOCUMENTOS = json.load(arq)

        # Elementos Wandb
        self.WANDB_PREFIXO=''
        self.WANDB_NOME_PROJETO="assistente-busca"  
        self.WANDB_TIPO_EXECUCAO="producao"

        self.CONFIGS={
            'cliente_llm': self.CLIENTE_LLM,
            'modelo_llm': self.MODELO_LLM,
            'modelo_funcao_de_embeddings': self.MODELO_FUNCAO_DE_EMBEDDINGS,
            'banco_vetorial':{
                'url': self.URL_BANCO_VETORES,
                'colecao': self.NOME_COLECAO_DE_DOCUMENTOS
            }
        }

        self.WANDB_ARTEFATO_BANCO_VETORIAL=f"{self.WANDB_PREFIXO}/{self.WANDB_NOME_PROJETO}/banco-vetorial-chroma:latest",
        #AFAZER: colocar artefato do prompt

configuracoes = Environment()
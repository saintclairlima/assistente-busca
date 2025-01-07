import json
import os
from dotenv import load_dotenv

url_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
url_dotenv = os.path.join(url_raiz_projeto, ".env")
load_dotenv(url_dotenv)

class Environment:
    def __init__(self):
        self.URL_BANCO_VETORES = os.getenv('URL_BANCO_VETORES')
        self.URL_OLLAMA=os.getenv('URL_OLLAMA')
        self.URL_HOST=os.getenv('URL_HOST')
        self.TAGS_SUBSTITUICAO_HTML={
            'TAG_INSERCAO_URL_HOST': self.URL_HOST
            }

        self.THREADPOOL_MAX_WORKERS=int(os.getenv('THREADPOOL_MAX_WORKERS'))
        self.NOME_COLECAO_DE_DOCUMENTOS=os.getenv('COLECAO_DE_DOCUMENTOS')
        self.EMBEDDING_INSTRUCTOR=os.getenv('EMBEDDING_INSTRUCTOR')
        self.EMBEDDING_SQUAD_PORTUGUESE=os.getenv('EMBEDDING_SQUAD_PORTUGUESE')
        self.MODELO_OLLAMA=os.getenv('MODELO_OLLAMA')
        self.DEVICE=os.getenv('DEVICE') # ['cpu', cuda']
        self.NUM_DOCUMENTOS_RETORNADOS=int(os.getenv('NUM_DOCUMENTOS_RETORNADOS'))

        self.MODELO_DE_EMBEDDINGS = self.EMBEDDING_INSTRUCTOR

        self.CONTEXTO_BASE = []
        with open(os.getenv('URL_INDICE_DOCUMENTOS'), 'r') as arq:
            self.DOCUMENTOS = json.load(arq)

environment = Environment()
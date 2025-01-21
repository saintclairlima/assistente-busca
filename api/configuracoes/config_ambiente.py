import os
import json
from dotenv import load_dotenv


url_raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
url_dotenv = os.path.join(url_raiz_projeto, ".env")
load_dotenv(url_dotenv)

class ConfiguracoesAmbiente:
    def __init__(self):
        self.url_llm=os.getenv('URL_LLM')
        self.url_host=os.getenv('URL_HOST')
        self.url_banco_sql=os.getenv('URL_BANCO_SQL')
        self.porta_banco_sql=os.getenv('PORTA_BANCO_SQL')
        self.usuario_banco_sql=os.getenv('USER_BANCO_SQL')
        self.senha_banco_sql=os.getenv('SENHA_BANCO_SQL')
        self.database_banco_sql=os.getenv('DATABASE_BANCO_SQL')
        
        self.device=os.getenv('DEVICE') # ['cpu', cuda']
        self.ambiente_execucao=os.getenv('AMBIENTE_EXECUCAO')
        
    def configuracoes_ambiente(self) -> dict:
        return {
            'device': self.device,
            'ambiente_execucao': self.ambiente_execucao
        }
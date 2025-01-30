import os
import json


class ConfiguracoesWeightsAndBiases:
    def __init__(self):

        with open('api/configuracoes/arq_conf.json', 'r', encoding='utf-8') as arq:
            configs = json.load(arq)
        
        self.usar_wandb = configs['usar_wandb']
        self.wandb_equipe = configs['wandb_equipe']
        self.wandb_nome_projeto = configs['wandb_nome_projeto']
        self.wandb_tipo_execucao = configs['wandb_tipo_execucao']
        self.wandb_uri_artefato_banco_vetorial = f'{self.wandb_equipe}/{self.wandb_nome_projeto}/banco-vetorial-chroma:latest'
        self.wandb_uri_artefato_prompt_mensagens = f'{self.wandb_equipe}/{self.wandb_nome_projeto}/prompts-mensagens:latest'

        if configs['openai_api_key']:
            os.environ['OPENAI_API_KEY'] = configs['openai_api_key']
        if configs['wandb_api_key']:
            os.environ['WANDB_API_KEY'] = configs['wandb_api_key']
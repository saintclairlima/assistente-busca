

class ConfiguracoesWeightsAndBiases:
    def __init__(self):
        
        self.usar_wandb=False
        self.wandb_equipe='cleiane-projetos' # grumpyai
        self.wandb_nome_projeto='assistente-busca'
        self.wandb_tipo_execucao='producao'
        self.wandb_uri_artefato_banco_vetorial=f'{self.wandb_equipe}/{self.wandb_nome_projeto}/banco-vetorial-chroma:latest',
        # AFAZER: colocar artefato do prompt
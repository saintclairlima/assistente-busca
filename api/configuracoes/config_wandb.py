

class ConfiguracoesWeightsAndBiases:
    def __init__(self):
        
        self.usar_wandb=True
        self.wandb_prefixo='cleiane-projetos' # grumpyai
        self.wandb_nome_projeto='assistente-busca'
        self.wandb_tipo_execucao='producao'

        self.wandb_logs={
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

        self.wandb_uri_artefato_banco_vetorial=f'{self.wandb_prefixo}/{self.wandb_nome_projeto}/banco-vetorial-chroma:latest',
        # AFAZER: colocar artefato do prompt
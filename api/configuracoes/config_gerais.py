from api.configuracoes.config_wandb import ConfiguracoesWeightsAndBiases
from api.configuracoes.config_ambiente import ConfiguracoesAmbiente
from api.configuracoes.config_aplicacao import ConfiguracoesAplicacao

class ConfiguracoesGerais(ConfiguracoesAmbiente, ConfiguracoesAplicacao, ConfiguracoesWeightsAndBiases):
    def __init__(self):
        ConfiguracoesAmbiente.__init__(self)
        ConfiguracoesAplicacao.__init__(self)
        ConfiguracoesWeightsAndBiases.__init__(self)
        
        self.tags_substituicao_html={
            'TAG_INSERCAO_URL_HOST': self.url_host
            }

configuracoes = ConfiguracoesGerais()
from api.configuracoes.config_wandb import ConfiguracoesWeightsAndBiases
from api.configuracoes.config_ambiente import ConfiguracoesAmbiente
from api.configuracoes.config_aplicacao import ConfiguracoesAplicacao

class ConfiguracoesGerais(ConfiguracoesAmbiente, ConfiguracoesAplicacao, ConfiguracoesWeightsAndBiases):
    def __init__(self):
        ConfiguracoesAmbiente.__init__(self)
        ConfiguracoesAplicacao.__init__(self)
        ConfiguracoesWeightsAndBiases.__init__(self)
        
        self.tags_substituicao_html={
            'TAG_INSERCAO_URL_HOST': self.url_host,
            'TAG_INSERCAO_MOSTRAR_CAMPO_COMENTARIO': self.permitir_comentarios
        }
    def sumarizar_configuracoes(self) -> dict:
        sumario = self.configuracoes_ambiente()
        sumario.update(self.configuracoes_banco_vetores())
        sumario.update(self.configuracoes_llm())
        
        return sumario

configuracoes = ConfiguracoesGerais()
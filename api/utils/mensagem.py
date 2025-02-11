from typing import Any, TypedDict
import json

class DadosMensagem(TypedDict):
    tag: str
    conteudo: Any = None
    # Represents data related to a message, containing 'tag' and optional 'conteúdo'

class Mensagem:
    def __init__(self, tipo: str, descricao: str = None):
        self.tipo = tipo
        self.descricao = descricao
        # Initializes a message with its type and description

    def json(self) -> str:
        return json.dumps(
            {
                'tipo': self.tipo,
                'descricao': self.descricao
            },
            ensure_ascii=False
        )
        # Returns the message as JSON with ASCII fallback disabled

class MensagemInfo(Mensagem):
    def __init__(self, descricao: str, mensagem: str = None):
        super().__init__('info', descricao)
        self.mensagem = mensagem
        # Initializes an info-type message with description and optional message content

    def json(self) -> str:
        return json.dumps(
            {
                'tipo': self.tipo,
                'descricao': self.descricao,
                'mensagem': self.mensagem
            },
            ensure_ascii=False
        )
        # Returns the info message as JSON, including its content

class MensagemErro(Mensagem):
    def __init__(self, descricao: str, mensagem: str = None):
        super().__init__('erro', descricao)
        self.mensagem = mensagem
        # Initializes an error-type message with description and optional message content

    def json(self) -> str:
        return json.dumps(
            {
                'tipo': self.tipo,
                'descricao': self.descricao,
                'mensagem': self.mensagem
            },
            ensure_ascii=False
        )
        # Returns the error message as JSON, including its content

class MensagemControle(Mensagem):
    def __init__(self, descricao: str, dados: DadosMensagem = None, mensagem: str = None):
        super().__init__('controle', descricao)
        self.mensagem = mensagem
        self.dados = dados
        # Initializes a control-type message with description, optional content, and data

    def json(self) -> str:
        return json.dumps(
            {
                'tipo': self.tipo,
                'descricao': self.descricao,
                'mensagem': self.mensagem,
                'dados': {
                    'tag': self.dados['tag'],
                    'conteudo': self.dados['conteudo']
                }
            },
            ensure_ascii=False
        )
        # Returns the control message as JSON, including its data details

class MensagemDados(Mensagem):
    def __init__(self, descricao: str, dados: DadosMensagem, mensagem: str = None):
        super().__init__('dados', descricao)
        self.mensagem = mensagem
        self.dados = dados
        # Initializes a data-type message with description and data content

    def json(self) -> str:
        return json.dumps(
            {
                'tipo': self.tipo,
                'descricao': self.descricao,
                'mensagem': self.mensagem,
                'dados': {
                    'tag': self.dados['tag'],
                    'conteudo': self.dados['conteudo']
                }
            },
            ensure_ascii=False
        )
        # Returns the data message as JSON, including its content details

from typing import Any, TypedDict
import json

class DadosMensagem(TypedDict):
    tag: str
    conteudo: Any = None

class Mensagem:
    def __init__(
        self,
        tipo: str,
        descricao: str = None):
            self.tipo=tipo
            self.descricao=descricao
            
    def json(self):
        return json.dumps(
            {
                'tipo': self.tipo,
                'descricao': self.descricao
            }, ensure_ascii=False
        )

class MensagemInfo(Mensagem):
    def __init__(self,
        descricao: str,
        mensagem: str = None):
            super().__init__('info', descricao)
            self.mensagem=mensagem

    def json(self):
        return json.dumps(
            {
                'tipo': self.tipo,
                'descricao': self.descricao,
                'mensagem': self.mensagem
            }, ensure_ascii=False
        )

class MensagemErro(Mensagem):
    def __init__(self,
        descricao: str,
        mensagem: str = None):
            super().__init__('erro', descricao)
            self.mensagem=mensagem

    def json(self):
        return json.dumps(
            {
                'tipo': self.tipo,
                'descricao': self.descricao,
                'mensagem': self.mensagem
            }, ensure_ascii=False
        )

class MensagemControle(Mensagem):
    def __init__(self,
        descricao: str,
        dados: DadosMensagem = None,
        mensagem: str = None):
            super().__init__('controle', descricao)
            self.mensagem=mensagem
            self.dados=dados

    def json(self):
        return json.dumps(
            {
                'tipo': self.tipo,
                'descricao': self.descricao,
                'mensagem': self.mensagem,
                'dados': {
                    'tag': self.dados['tag'],
                    'conteudo': self.dados['conteudo']
                    }
            }, ensure_ascii=False
        )

class MensagemDados(Mensagem):
    def __init__(self,
        descricao: str,
        dados: DadosMensagem,
        mensagem: str = None):
            super().__init__('dados', descricao)
            self.mensagem=mensagem
            self.dados=dados

    def json(self):
        return json.dumps(
            {
                'tipo': self.tipo,
                'descricao': self.descricao,
                'mensagem': self.mensagem,
                'dados': {
                    'tag': self.dados['tag'],
                    'conteudo': self.dados['conteudo']
                    }
            }, ensure_ascii=False
        )

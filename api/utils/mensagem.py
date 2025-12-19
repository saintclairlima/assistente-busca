from typing import Any, TypedDict
import json

class DadosMensagem(TypedDict):
    # Represents data related to a message, containing 'tag' and optional 'conteúdo'
    '''
    Classe que estrutura dados a serem incluídos em mensagens de comunicação da API para o APP.

    tag -- marcador utilizado para facilitar controle no APP
    conteudo -- dados a serem enviados
    '''

    tag: str
    conteudo: Any = None

class Mensagem:
    '''
    Classe que encapsula os dados e metadados a serem enviados ao APP
    
    Atributos:
        tipo (str): o tipo de mensagem criada. Os tipos usados nesta aplicação são
            'info': ideal para logs;
            'erro': notifica ocorrência de erros;
            'controle': mensagens utilizadas para controle no APP; e
            'dados': informações solicitadas pelo APP.
        descricao (str): uma breve descrição que semanticamente resuma a mensagem.
    '''

    def __init__(self, tipo: str, descricao: str = None):
        # Initializes a message with its type and description
        '''Inicializa a mensagem com tipo e descrição
        
        Parâmetros:
            tipo (str): o tipo da mensagem criada (info, erro, controle, dados)
            descricao (str): descrição semântica da mensagem
        '''

        self.tipo = tipo
        self.descricao = descricao

    def json(self) -> str:
        # Returns the message as JSON with ASCII fallback disabled
        '''Cria a mensagem em formato JSON sem enforçar caracteres ASCII
        
        Retorna:
            str: Uma string da representação da mensagem em JSON.
        '''

        return json.dumps(
            {
                'tipo': self.tipo,
                'descricao': self.descricao
            },
            ensure_ascii=False
        )

class MensagemInfo(Mensagem):
    '''
    Especialização da classe Mensagem, voltada para enviar dados de Logs para o APP
    
    Atributos:
        mensagem (str): conteúdo opcional, voltado para eventual apresentação na interface de usuário
    '''
    
    def __init__(self, descricao: str, mensagem: str = None):        
        # Initializes an info-type message with description and optional message content
        '''Inicializa a mensagem do tipo 'info' com descrição e mensagem opcional
        
        Parâmetros:
            descricao (str): descrição semântica da mensagem
            mensagem (str): parâmetro opcional, voltado para eventual apresentação na interface de usuário
        '''

        super().__init__('info', descricao)
        self.mensagem = mensagem

    def json(self) -> str:
        # Returns the info-type message as JSON with ASCII fallback disabled
        '''Cria a mensagem do tipo 'info' em formato JSON sem enforçar caracteres ASCII
        
        Retorna:
            str: Uma string da representação da mensagem em JSON.
        '''

        return json.dumps(
            {
                'tipo': self.tipo,
                'descricao': self.descricao,
                'mensagem': self.mensagem
            },
            ensure_ascii=False
        )

class MensagemErro(Mensagem):
    '''
    Especialização da classe Mensagem, voltada para notificar o APP sobre erros ocorridos na API
    
    Atributos:
        mensagem (str): conteúdo opcional, voltado para eventual apresentação na interface de usuário
    '''

    def __init__(self, descricao: str, mensagem: str = None):
        # Initializes an error-type message with description and optional message content
        '''Inicializa a mensagem do tipo 'erro' com descrição e mensagem opcional
        
        Parâmetros:
            descricao (str): descrição do erro
            mensagem (str): parâmetro opcional, voltado para eventual apresentação na interface de usuário
        '''

        super().__init__('erro', descricao)
        self.mensagem = mensagem

    def json(self) -> str:
        # Returns the error-type message as JSON with ASCII fallback disabled
        '''Cria a mensagem do tipo 'erro' em formato JSON sem enforçar caracteres ASCII
        
        Retorna:
            str: Uma string da representação da mensagem em JSON.
        '''

        return json.dumps(
            {
                'tipo': self.tipo,
                'descricao': self.descricao,
                'mensagem': self.mensagem
            },
            ensure_ascii=False
        )

class MensagemControle(Mensagem):
    '''
    Especialização da classe Mensagem, voltada para passar ao APP informações necessárias a controle de elementos no APP
    
    Atributos:
        dados (DadosMensagem): conteúdo opcional, contendo dados necessários para controle de elementos no APP
        mensagem (str): conteúdo opcional, voltado para eventual apresentação na interface de usuário
    '''

    def __init__(self, descricao: str, dados: DadosMensagem = None, mensagem: str = None):
        # Initializes a control-type message with description, optional content, and data
        '''Inicializa a mensagem do tipo 'controle' com descrição, dados opcionais e mensagem opcional
        
        Parâmetros:
            descricao (str): descrição semântica da mensagem
            dados (DadosMensagem): parâmetro opcional, contendo dados necessários para controle de elementos no APP
            mensagem (str): parâmetro opcional, voltado para eventual apresentação na interface de usuário
        '''

        super().__init__('controle', descricao)
        self.mensagem = mensagem
        self.dados = dados

    def json(self) -> str:
        # Returns the control-type message as JSON with ASCII fallback disabled
        '''Cria a mensagem do tipo 'controle' em formato JSON sem enforçar caracteres ASCII
        
        Retorna:
            str: Uma string da representação da mensagem em JSON.
        '''

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

class MensagemDados(Mensagem):
    '''
    Especialização da classe Mensagem, voltada para envio de dados solicitados pelo APP
    
    Atributos:
        dados (DadosMensagem): dados solicitados pelo APP
        mensagem (str): conteúdo opcional, voltado para eventual apresentação na interface de usuário
    '''
    
    def __init__(self, descricao: str, dados: DadosMensagem, mensagem: str = None):
        # Initializes a data-type message with description and data content
        '''Inicializa a mensagem do tipo 'dados' com descrição, dados e mensagem opcional
        
        Parâmetros:
            descricao (str): descrição semântica da mensagem
            dados (DadosMensagem): dados solicitados pelo APP
            mensagem (str): parâmetro opcional, voltado para eventual apresentação na interface de usuário
        '''

        super().__init__('dados', descricao)
        self.mensagem = mensagem
        self.dados = dados

    def json(self) -> str:
        # Returns the data message as JSON, including its content details
        '''Cria a mensagem do tipo 'dados' em formato JSON sem enforçar caracteres ASCII
        
        Retorna:
            str: Uma string da representação da mensagem em JSON.
        '''

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

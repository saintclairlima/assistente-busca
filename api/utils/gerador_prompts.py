
from typing import List
from api.configuracoes.config_gerais import configuracoes

class GeradorPrompts:

    def gerar_prompt_rag(pergunta: str, documentos: List[str], template=configuracoes.template_prompt_rag) -> str:
        # Creates formatted user prompt to be sent to the LLM API
        '''
        Gera prompt de usuário formatado para envio à API do LLM

        Parâmetros:
            pergunta (str): pergunta feita pelo usuário
            documentos (List[str]): lista de textos a serem utilizados como contexto para geração da resposta

        Retorna:
            (str) Prompt formatado conforme template contido no arquivo de configurações
        '''

        if template: return template.format('\n'.join(documentos), pergunta)
        else: return 'DOCUMENTOS:\n{}\nPERGUNTA: {}'.format('\n'.join(documentos), pergunta)

    def criar_marcador_idioma(pergunta: str) -> str:
        msg_sistema = f''''''
        msg_usuario = pergunta

        mensagens = [
            {'role': 'system', 'content': msg_sistema},
            {'role': 'user', 'content': msg_usuario}
        ]

        formato = {
            "type": "object",
            "properties": {
                "marcador-idioma": {"type": "string"},
                "intencao-usuario": {"type": "string"},
                "pergunta-frase-reformulada": {"type": "string"}
            },
            "required": ["pergunta", "intencao-usuario", "resposta"]
        }

        payload = {
            "model": configuracoes.modelo_llm,
            "messages": mensagens,
            "temperature": 0.0,
            "format": formato,
            "stream": False
        }
        
        resposta = requests.post(f'{configuracoes.url_llm}/api/chat', json=payload)
        dados = json.loads(resposta.content)
        dados = json.loads(dados['message']['content'])
        return dados
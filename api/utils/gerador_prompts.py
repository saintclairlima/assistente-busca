
import json
from typing import List

import requests
from api.configuracoes.config_gerais import configuracoes

class GeradorPrompts:

    def gerar_prompt_rag(pergunta: str, documentos: List[str], template=configuracoes.template_prompt_rag) -> str:
        # Creates formatted user prompt to be sent to the LLM API
        '''
        Gera prompt de usuário formatado para geração RAG com informações de documentos para envio à API do LLM

        Parâmetros:
            pergunta (str): pergunta feita pelo usuário
            documentos (List[str]): lista de textos a serem utilizados como contexto para geração da resposta

        Retorna:
            (str) Prompt formatado conforme template contido no arquivo de configurações
        '''

        if template: return template.format('\n'.join(documentos), pergunta)
        else: return configuracoes.templates_intencoes['consulta'].format('\n'.join(documentos), pergunta)

    def gerar_prompt_interacao(pergunta: str, intencao_usuario: str='generico', template=None) -> str:
        # Creates formatted user prompt to be sent to the LLM API
        '''
        Gera prompt de usuário formatado para envio à API do LLM

        Parâmetros:
            pergunta (str): pergunta feita pelo usuário

        Retorna:
            (str) Prompt formatado conforme template contido no arquivo de configurações
        '''

        if not template:
            templates_intencoes = configuracoes.templates_intencoes
            template = templates_intencoes.get(intencao_usuario, templates_intencoes['generica'])
        
        return template.format(pergunta)

    def criar_marcador_idioma(pergunta: str) -> str:
        msg_sistema = f'''Você é uma ferramenta de identificação de idioma de uma pergunta. Você deve analisar cuidadosamente a pergunta fornecida e identificar o idioma.
        Depois você deve gerar uma pequena mensagem, no idioma que for identificado, informando que a pergunta deve ser respondida usando o idioma identificado.
        EXEMPLO 1:
        Pergunta: O que significa a palavra Parlamento?
        
        Resultado esperado:
        idioma: português
        mensagem: "Responda a pergunta em português"

        EXEMPLO 2:
        Pergunta: How long does a deputy's term take?
        
        Resultado esperado:
        idioma: English
        mensagem: "Answer the question in English"

        

        EXEMPLO 3:
        Pergunta: Wer ist der Vorsitzende der gesetzgebenden Versammlung?
        
        Resultado esperado:
        idioma: Deutsch
        mensagem: "Antworten Sie die Frage auf deutsch?"
        '''
        msg_usuario = f"Identifique o idioma da seguinte pergunta e me informe em que idioma ela deve ser respondida: {pergunta}"

        mensagens = [
            {'role': 'system', 'content': msg_sistema},
            {'role': 'user', 'content': msg_usuario}
        ]

        formato = {
            "type": "object",
            "properties": {
                "idioma": {"type": "string"},
                "mensagem": {"type": "string"}
            },
            "required": ["idioma", "mensagem"]
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

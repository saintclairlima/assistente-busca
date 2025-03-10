
import json
from typing import List

import requests
from api.configuracoes.config_gerais import configuracoes
from api.utils.interface_llm import InterfaceOllama

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

    def otimizar_prompt(frase, historico):
        msg_sistema = f'''
        Você é um agente que atua na otimização do funcionamento de um sistema de recuperação de dados, semelhante a um chatbot, usando uma pergunta ou frase de busca dos usuários para recuperar as informações.
        As perguntas ou frases de busca dos usuários são enviadas a uma vector store para recuperação de documentos.
        Com cada pergunta/frase, você recebe um contexto com as perguntas/frases de busca anteriores, bem como as informações recuperadas.
        Seu objetivo é garantir que a pergunta/frase do usuário esteja clara o suficiente para recuperar documentos relevantes da vector store.
        Você deve analisar a frase/pergunta do usuário, examinar a necessidade de reformulá-la e utilizar o contexto de mensagens anteriores para fazer as alterações necessárias.

        Considerando a frase/pergunta, faça o seguinte:
        Analise a frase/pergunta;
        Identifique a intenção do usuário (que informações ele está procurando?);
        Avalie se a frase/pergunta está adequada para realizar uma busca por documentos na vector store (a vector store vai ser capaz de buscar as informações que ele deseja?);
        Avalie se a frase/pergunta está clara, coerente, coesa (a frase é suficientemente clara e específica para recuperar documentos da vector store?).

        Se a pergunta não estiver adequada, você deve reformulá-la, garantindo que ela esteja adequada para uma busca numa vector store.

        Para reformular a frase/pergunta, faça o seguinte:
        * Analise o contexto e veja se há informações nele que estejam implícitas na frase/pergunta analisada. Se for o caso, complete a frase/pergunta com a informação que falta. Por exemplo:
        CONTEXTO:
        {[{'role': 'user', 'content': 'Quanto tempo dura uma legislatura?'},
        {'role': 'assistant', 'content': 'Uma legislatura dura quatro anos.'}]}
        PERGUNTA: "E uma seção ordinária?"
        A sua resposta deve ser: 
        '{{"pergunta-frase-original": "E uma seção ordinária?", "intencao-usuario": "Saber qual é o tempo de duração de uma seção ordinária?", "pergunta-frase-reformulada": "Quanto tempo dura uma seção ordinária?"}}'

        * Quando a frase estiver com erro de grafia, você deve corrigir. Por exemplo:
        CONTEXTO:
        []
        FRASE: "QUEM TEM DIREITO ÀLICENÇA PREMIO"
        A sua resposta deve ser: 
        '{{"pergunta-frase-original": "QUEM TEM DIREITO ÀLICENÇA PREMIO", "intencao-usuario": "Saber que pessoa tem direito a receber a licença prêmio", "pergunta-frase-reformulada": "Quem tem direito à licença prêmio?"}}'

        * Somente nos casos em que a pergunta não for clara você deve sugerir alteração. Evite ao máximo sugerir alterações desnecessárias.
        * Se não foi encontrado motivo para reformular, não gere uma frase reformulada. Nesse caso o campo "pergunta-frase-reformulada" deve ter uma string vazia como valor. Por exemplo:
        CONTEXTO:
        []
        PERGUNTA: "Quanto tempo dura uma legislatura?"
        A sua resposta deve ser:
        '{{"pergunta-frase-original": "Quanto tempo dura uma legislatura?", "intencao-usuario": "Saber qual é o tempo de duração de uma seção ordinária?", "pergunta-frase-reformulada": ""}}'
        
        * Na sua reformulação, não inclua nada que não possa ser inferido do contexto. Não faça reformulações desnecessárias!
        
        '''


        msg_usuario = f'''
        Considere a seguinte FRASE/PERGUNTA:
        "{frase}"

        Considere o seguinte CONTEXTO de mensagens anteriores entre o usuário e um LLM assistente:
        "{historico}"

        Analise a FRASE/PERGUNTA e, se for necessário, reformule-a para que fique clara e com as informações necessárias para recuperar documentos numa vector store.

        Vamos começar!
        
        '''

        mensagens = [
            {'role': 'system', 'content': msg_sistema},
            {'role': 'user', 'content': msg_usuario}
        ]

        formato = {
            "type": "object",
            "properties": {
                "pergunta-frase-original": {"type": "string"},
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
    
# msgs = [{'role': 'user', 'content': 'Quantas são as comissões permanentes da ALRN?'},
#         {'role': 'assistant', 'content': 'A ALRN tem 10 comissões permanentes'}]
# msg='Quais as funções delas?'
# gp.otimizar_prompt(msg, msgs)
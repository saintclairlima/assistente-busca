
from typing import List
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

    async def otimizar_prompt(frase, historico):
        sistema = '''
        Você auxilia o setor de informações da Assembleia Legislativa do Rio Grande do Norte a responder perguntas dos servidores e cidadãos sobre a Assembleia.
        As perguntas ou frases de busca dos usuários são enviadas a um vector store para recuperação de documentos. Seu objetivo é garantir que a pergunta do
        usuário esteja clara o suficiente para recuperar documentos relevantes da vector store. Para isso, você deve analisar uma frase e examinar a necessidade
        de reformulá-la e utilizar o contexto de mensagens anteriores.'''


        mensagem = f'''
        Considere a seguinte FRASE/PERGUNTA:
        "{frase}"

        Considere o seguinte CONTEXTO de mensagens anteriores entre o usuário e um LLM assistente:
        "{historico}"

        Identifique a intenção do usuário (que informações ele está procurando?);
        Avalie se a frase/pergunta está adequada para realizar uma busca por documentos na vector store (a vector store vai ser capaz de buscar as informações que ele deseja?);
        Avalie se a frase/pergunta está clara, coerente, coesa (a frase é suficientemente clara e específica para recuperar documentos da vector store?).

        Se a pergunta não estiver adequada, você deve reformulá-la, garantindo que ela esteja adequada para uma busca numa vector store.

        Para isso você é obrigado a fazer o seguinte:
        * Somente nos casos em que a pergunta não for clara você deve sugerir alteração. Evite ao máximo sugerir alterações desnecessárias.
        * Quando necessário, você deve reformular a frase, utilizando somente o contexto, de forma que ela seja coerente e coesa. Não inclua nenhum elemento que não se baseie no contexto
        * Se não foi encontrado motivo para reformular, a saída deve ser uma string vazia: {'""'}.

        <Exemplo 1>
        Contexto:
        [{'role': 'user', 'content': 'Eu gosto de bananas e sou torcedor do palmeiras. Meu irmão gosta de maçã e torce pelo Flamengo. Lembre-se disso'},
        {'role': 'assistant', 'content': 'Ok. Vou me lembrar disso'},
        {'role': 'user', 'content': 'Eu gosto de qual fruta?'},
        {'role': 'assistant', 'content': 'Você gosta de bananas.'}]
        Frase: "E meu irmão?"
        A sua resposta deve ser: "Meu irmão gosta de qual fruta?"
        <Fim do Exemplo 1>
        
        <Exemplo 2>
        Contexto:
        [{'role': 'user', 'content': 'Como se fala "Eu estou com fome" em alemão?'},
        {'role': 'assistant', 'content': '"Eu estou com fome" em alemão é "Ich habe hunger"'}]
        Frase: "E como se diz 'Eu estou com sede' em alemão?"
        A sua resposta deve ser: "E como se diz 'Eu estou com sede' em alemão?"
        <Fim do Exemplo 2>
        
        <Exemplo 3>
        Contexto:
        []
        Frase: "Quanto tempo dura uma legislatura?"
        A sua resposta deve ser: "Quanto tempo dura uma legislatura?"
        <Fim do Exemplo 3>
        '''

        formato = {
            "type": "object",
            "properties": {
                "pergunta-frase-original": {"type": "string"},
                "pergunta-frase-reformulada": {"type": "string"}
            },
            "required": ["pergunta", "resposta"]
        }

        payload = {
            "model": configuracoes.modelo_llm,
            "messages": mensagens,
            "temperature": 0.0,
            "format": formato,
            "stream": False
        }
        
        resposta = requests.post(self.url_llm, json=payload)
        dados = json.loads(resposta.content)
        return dados['message']['content']
        
        interface_llm = InterfaceOllama(
            url_ollama=configuracoes.url_llm,
            nome_modelo=configuracoes.modelo_llm,
            definicoes_sistema=sistema,
            top_k=10,
            top_p=0.5)
        prompt=f'''Contexto:\n{str(historico)}\nFrase: {frase}'''
        frase_reformulada = interface_llm.gerar_resposta_llm(prompt, [])

        return frase_reformulada['message']['content']
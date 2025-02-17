
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
        sistema = '''Você é uma ferramenta de reformulação de frases com base em contexto. Dado um contexto e uma dada frase, você deve analisar a frase e ver se ela tem sentido por si só ou se precisa de contexto para fazer sentido.
        Somente nos casos em que a pergunta não for clara você deve sugerir alteração. Evite ao máximo sugerir alterações desnecessárias.
        Quando necessário, você deve reformular a frase, utilizando somente o contexto, de forma que ela seja coerente e coesa. Não inclua nenhum elemento que não se baseie no contexto
        Se for feita modificação, a saída deve ter apenas a pergunta reformulada, sem qualquer comentário.
        Se não foi encontrado motivo para reformular, a saída deve ser a frase original.

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
        
        interface_llm = InterfaceOllama(
            url_ollama=configuracoes.url_llm,
            nome_modelo=configuracoes.modelo_llm,
            definicoes_sistema=sistema,
            top_k=10,
            top_p=0.5)
        prompt=f'''Contexto:\n{str(historico)}\nFrase: {frase}'''
        frase_reformulada = ''
        async for item in interface_llm.gerar_resposta_llm(prompt, []):
            frase_reformulada += item['message']['content']
        
        return frase_reformulada
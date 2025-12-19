import argparse
from typing import List
import chromadb
import requests
import json
from api.configuracoes.config_gerais import configuracoes

class GeradorPerguntas:
    def __init__(self, url_llm, modelo_llm):
        self.url_llm = url_llm
        self.modelo_llm = modelo_llm

    def gerar_perguntas_artigo(self, artigo):

        '''Gera uma lista de perguntas e respostas com base em um texto. É utilizado um LLM para realizar a geração

        Parâmetros:
            artigo (str): texto base a ser utilizado para gerar as perguntas

        Retorna:
            (List[dict]): lista de dicionários com uma pergunta e uma resposta por entrada no formato: 
        ```python
        [ {"pergunta": str, "trecho_resposta": str} ]
        ```

        '''
        
        msg_sistema = '''
        Você auxilia o setor de informações da Assembleia Legislativa do Rio Grande do Norte a responder perguntas dos servidores e cidadãos sobre a Assembleia. Sua função é
        ajudar a criar um banco de dados sintético com perguntas frequentes e dúvidas que servidores reais do serviço público poderiam ter. Esse banco de dados será usado para
        treinar uma aplicação que vai responder perguntas reais de servidores, portanto deve ter perguntas pertinentes e o mais próximo possível de dúvidas reais relacionadas aos
        temas de regulação de uma Assembleia Legislativa.'''

        msg_usuario = f'''
        Considere o texto a seguir, que é um artigo de uma lei:
        
        {artigo}
        
        Agora extraia as informações do artigo e gere perguntas que possam ser respondidas com base no conteúdo textual do artigo.
        Além disso, formule a resposta com base no artigo e em nenhuma outra fonte. As perguntas e respostas serão utilizadas para treinamento e finetuning de um LLM. Siga as seguintes diretrizes para gerar as perguntas e respostas:

        Considere o texto recebido e identifique informações significativas;
        Com base nas informações, crie pelo menos 3 perguntas que possam ser respondidas com base no conteúdo do texto;
        Caso o texto fornecido não tenha informação a partir da qual seja possível criar perguntas relevantes, deve ser retornado um objeto vazio;
        As perguntas devem ser claras, diretas, e específicas;
        As perguntas podem ter sinônimos ou termos aproximados do texto base, mas devem ser possível de ser respondidas pelo texto fornecido;
        Para cada pergunta, formule uma resposta usando como base o conteúdo do artigo, sem utilizar qualquer outro conhecimento que você disponha.

        Cada pergunta será aceitável somente se:

        * Estiver relacionada aos assuntos pertinentes ao artigo apresentado
        * For uma pergunta relevante, semelhante ao que seria perguntado por uma pessoa vim dúvida
        * Puder ser respondida usando o fragmento apresentado

        O resultado deve ser em formato estruturado.

        Um exemplo de como devem ser geradas as perguntas:

        Exemplo de texto base:
        "Art. 1º A Assembleia Legislativa é composta de Deputados, representantes do povo norte-rio-grandense, eleitos, na forma da lei, para mandato de 4 (quatro) anos."

        Resultado aceitável:
            {[
                {
                    "pergunta": "A Assembleia Legislativa é formada pelo que?",
                    "resposta": "A Assembleia Legislativa é composta por Deputados, que são eleitos pelo do povo norte-rio-grandense e os representam.",
                },
                {
                    "pergunta": "O que é um Deputado?",
                    "resposta": "Um Deputado é um representante eleito do povo, possuindo mandato de quatro anos.",
                },
                {
                    "pergunta": "Quanto tempo dura um mandato?",
                    "resposta": "Um mandato dura pelo período de quatro anos.",
                }
            ]}

        Caso o texto não tenha conteúdo relevante, o resultado deve ser um objeto vazio {{}}.

        Vamos começar?'''
        
        mensagens = [
            {'role': 'system', 'content': msg_sistema},
            {'role': 'user', 'content': msg_usuario}
        ]


        formato = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pergunta": {"type": "string"},
                    "resposta": {"type": "string"}
                },
                "required": ["pergunta", "resposta"]
            }
        }

        
        payload = {
            "model": self.modelo_llm,
            "messages": mensagens,
            "temperature": 0.0,
            "format": formato,
            "stream": False
        }
        
        resposta = requests.post(self.url_llm, json=payload)
        dados = json.loads(resposta.content)
        return dados['message']['content']

    def gerar_perguntas_banco_vetorial(self, url_banco_vetorial: str, nome_colecao: str, url_arquivo_saida: str) -> List[dict]:

        '''
        Gera uma lista de perguntas para cada um dos fragmentos em um banco vetorial

        Parâmetros:
            url_banco_vetorial (str): a url do banco de vetores a ser usado como base
            nome_colecao (str): nome da coleção a ser usada, existente no banco
            url_arquivo_saida (str): caminho em que será salvo o arquivo com o resultado

        Retorna:
            Retorna uma lista de documentos na coleção, acrescentados de uma lista de perguntas
        
        O formato da lista retornada é o seguinte:
        [{
            "id": str,
            "page_content": str,
            "metadata": dict,
            "perguntas": [ { "pergunta": str, "trecho_resposta": str } ]
        }]
        '''

        try:
            with open(url_arquivo_saida, 'r', encoding='utf-8') as arq:
                documentos = json.load(arq)
                print(f'Carregados dados em {url_arquivo_saida}')

        except FileNotFoundError:
            print(f'Consultando documentos do banco de vetores')
            client = chromadb.PersistentClient(path=url_banco_vetorial)
            collection = client.get_collection(name=nome_colecao)
            registros = collection.get()
            registros = zip(registros['ids'], registros['documents'], registros['metadatas'])
            documentos = [ {
                    "id": r[0],
                    "page_content": r[1],
                    "metadata": r[2]
                } for r in registros]

            print(f'Salvando resultados em {url_arquivo_saida}')
            with open(url_arquivo_saida, 'w', encoding='utf-8') as arq:
                json.dump(documentos, indent=4, ensure_ascii=False)
                
            client._system.stop()

        qtd_docs = len(documentos)
        
        print(f'Gerando perguntas para {qtd_docs} documentos')
        for idx in range(qtd_docs):
            print(f'\rProcessando documento {idx+1} de {qtd_docs}', end='')
            doc = documentos[idx]
            if 'perguntas' not in doc:
                perguntas = self.gerar_perguntas_artigo(artigo=doc['page_content'])
                doc['perguntas'] = json.loads(perguntas)
                
                with open(url_arquivo_saida, 'w', encoding='utf-8') as arq:
                    arq.write(json.dumps(documentos, indent=4, ensure_ascii=False))
        
        return documentos
                
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera um conjunto de perguntas a partir de documentos armazenados em um banco vetorial")
    parser.add_argument('--url_banco_vetorial', type=str, required=True, help="nome do banco de vetores a ser consultado")
    parser.add_argument('--nome_colecao', type=str, required=True, help='''nome da coleção a ser consultada''')
    parser.add_argument('--url_arquivo_saida', type=str, required=True, help='url do arquivo em que vão ser salvos os resultados')
    parser.add_argument('--modelo_llm', type=str, help="modelo de LLM a ser utilizado")
    parser.add_argument('--url_llm', type=str, help="url da api em que o modelo está sendo executado")
    args = parser.parse_args()
    
    url_banco_vetorial = configuracoes.url_banco_vetores if not args.url_banco_vetorial else args.url_banco_vetorial
    nome_colecao = configuracoes.nome_colecao_de_documentos + '/api/chat' if not args.nome_colecao else args.nome_colecao
    url_arquivo_saida = f'documentos_perguntas_{nome_colecao}.json' if not args.url_arquivo_saida else args.url_arquivo_saida
    modelo_llm = configuracoes.modelo_llm if not args.modelo_llm else args.modelo_llm
    url_llm = configuracoes.url_llm + '/api/chat' if not args.url_llm else args.url_llm
    
    print(f'Iniciando gerador de perguntas (modelo: "{modelo_llm}", url: "{url_llm}")')
    gerador_perguntas = GeradorPerguntas(modelo_llm=modelo_llm, url_llm=url_llm)
    gerador_perguntas.gerar_perguntas_banco_vetorial(
        url_banco_vetorial=url_banco_vetorial,
        nome_colecao=nome_colecao,
        url_arquivo_saida=url_arquivo_saida)
    
## Modelo de execução
#python -m api.testes.gerador_perguntas --url_banco_vetorial "api/dados/bancos_vetores/banco_assistente" --nome_colecao "documentos_rh" --url_arquivo_saida "api/testes/perguntas_documentos_rh.json" --modelo_llm "llama3.1" --url_llm "http://10.90.6.15:11434"
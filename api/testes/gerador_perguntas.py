## AFAZER: Ajustar para dar conta das alteraç~eos feitas nas classes usadas
import argparse
import os
import chromadb
import requests
import json
import sys
from torch import cuda
from api.configuracoes.config_gerais import configuracoes

class GeradorPerguntas:
    def __init__(self, url_llm, modelo_llm):
        self.url_llm = url_llm
        self.modelo_llm = modelo_llm

    def gerar_perguntas_artigo(self, artigo):
        prompt = f'''
        Você é uma ferramenta de geração de perguntas com base em um contexto. Seu objetivo é receber o texto de um artigo de uma lei,
        extrair as informações do artigo e gerar perguntas que possam ser respondidas com trechos do artigo, assim como detectar o trecho
        do artigo que responde cada pergunta. As perguntas e respostas serão utilizadas para treinamento e finetuning de um LLM.
        Siga as seguintes diretrizes para gerar as perguntas:

        Considere o texto recebido e identifique informações significativas;
        Com base nas informações, crie pelo menos 3 perguntas que possam ser respondidas com fragmentos do texto;
        Caso seja possível mais que 3 perguntas, limite a quantidade de perguntas geradas a até 5;
        As perguntas devem ser claras, diretas, e específicas;
        As perguntas podem ter sinônimos ou termos aproximados do texto base, mas devem ser possível de ser respondidas pelo texto fornecido;
        Para cada pergunta, identifique o trecho do texto que serve como resposta.

        O resultado deve ser em formato estruturado.

        Um exemplo de como deve ser geradas as perguntas:

        Texto de exemplo:
        "Art. 1º A República Federativa do Brasil, formada pela união indissolúvel dos Estados e Municípios e do Distrito Federal, constitui-se em Estado Democrático de Direito e tem como fundamentos:
        I - a soberania;
        II - a cidadania
        III - a dignidade da pessoa humana;
        IV - os valores sociais do trabalho e da livre iniciativa;
        V - o pluralismo político.
        Parágrafo único. Todo o poder emana do povo, que o exerce por meio de representantes eleitos ou diretamente, nos termos desta Constituição."

        Resposta aceitável:
        {{
            "pergunta1": "O que forma a República  Federativa do Brasil?",
            "resposta1": "união indissolúvel dos Estados e Municípios e do Distrito Federal",
            "pergunta2": "Em que se constitui a República Federativa do Brasil?",
            "resposta2": "constitui-se em Estado Democrático de Direito",
            "pergunta3": "Quais os fundadmentos da República Federativa do Brasil?",
            "resposta3": "I - a soberania; II - a cidadania III - a dignidade da pessoa humana; IV - os valores sociais do trabalho e da livre iniciativa; V - o pluralismo político.",
            "pergunta4": "De onde emana todo o poder?",
            "resposta4": "Todo o poder emana do povo"
        }}

        TEXTO BASE: {artigo}'''


        formato = {
            "type": "object",
            "properties": {
                "pergunta1": {"type": "string"},
                "pergunta2": {"type": "string"},
                "pergunta3": {"type": "string"},
                "pergunta4": {"type": "string"},
                "pergunta5": {"type": "string"},
                "resposta1": {"type": "string"},
                "resposta2": {"type": "string"},
                "resposta3": {"type": "string"},
                "resposta4": {"type": "string"},
                "resposta5": {"type": "string"},
            },
            "required": ["pergunta1","resposta1","pergunta2","resposta2","pergunta3","resposta3"]
        }

        
        payload = {
            "model": self.modelo_llm,
            "prompt": prompt,
            "temperature": 0.0,
            "format": formato,
            "stream": False
        }
        
        resposta = requests.post(self.url_llm, json=payload)
        dados = json.loads(resposta.content)
        return dados['response']

    def gerar_perguntas_banco_vetorial(self, url_banco_vetorial: str, nome_colecao: str, url_arquivo_saida: str):
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
                arq.write(json.dumps(documentos, indent=4, ensure_ascii=False))
                
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
                
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera um conjunto de perguntas a partir de documentos armazenados em um banco vetorial")
    parser.add_argument('--url_banco_vetorial', type=str, required=True, help="nome do banco de vetores a ser consultado")
    parser.add_argument('--nome_colecao', type=str, required=True, help='''nome da coleção a ser consultada''')
    parser.add_argument('--url_arquivo_saida', type=str, required=True, help='url do arquivo em que vão ser salvos os resultados')
    parser.add_argument('--modelo_llm', type=str, help="modelo de LLM a ser utilizado")
    parser.add_argument('--url_llm', type=str, help="url da api em que o modelo está sendo executado")
    args = parser.parse_args()

    modelo_llm = configuracoes.modelo_llm if not args.modelo_llm else args.modelo_llm
    url_llm = configuracoes.url_llm + '/api/generate' if not args.url_llm else args.url_llm
    
    print(f'Iniciando gerador de perguntas (modelo: "{modelo_llm}", url: "{url_llm}")')
    gerador_banco_perguntas = GeradorPerguntas(modelo_llm=modelo_llm, url_llm=url_llm)
    gerador_banco_perguntas.gerar_perguntas_banco_vetorial(
        url_banco_vetorial=args.url_banco_vetorial,
        nome_colecao=args.nome_colecao,
        url_arquivo_saida=args.url_arquivo_saida)
    
## Modelo de execução
#python -m api.testes.gerador_perguntas --url_banco_vetorial "api/dados/bancos_vetores/banco_assistente" --nome_colecao "documentos_rh" --url_arquivo_saida "api/testes/perguntas_documentos_rh.json" --modelo_llm "llama3.1" --url_llm "http://10.90.6.15:11434"
import os
import chromadb
import requests
import json
import sys
from torch import cuda

from sentence_transformers import SentenceTransformer

from ..utils.utils import FuncaoEmbeddings
from ..configuracoes.config_gerais import configuracoes
URL_OLLAMA = 'http://localhost:11434/api/generate'
MODELO_OLLAMA='llama3.1'
URL_LOCAL = os.path.abspath(os.path.join(os.path.dirname(__file__), "../dados"))
EMBEDDING_INSTRUCTOR="hkunlp/instructor-xl"
URL_BANCO_VETORES=os.path.join(URL_LOCAL,"bancos_vetores/banco_vetores_regimento_resolucoes_rh")
NOME_COLECAO='regimento_resolucoes_rh'
DEVICE='cuda' if cuda.is_available() else 'cpu'

class GeradorPerguntas:
    def __init__(self,
                 url_ollama=URL_OLLAMA,
                 modelo_ollama=MODELO_OLLAMA,
                 url_local=URL_LOCAL,
                 nome_modelo=EMBEDDING_INSTRUCTOR,
                 url_banco_vetores=URL_BANCO_VETORES,
                 nome_colecao=NOME_COLECAO,
                 device=DEVICE):
        self.URL_OLLAMA = url_ollama
        self.MODELO_OLLAMA = modelo_ollama
        self.URL_LOCAL = url_local
        self.NOME_MODELO = nome_modelo
        self.URL_BANCO_VETORES = url_banco_vetores
        self.NOME_COLECAO = nome_colecao
        self.DEVICE = device

    def gerar_perguntas(self, artigo):
        prompt = '''Considere o artigo abaixo. Crie pelo menos 5 perguntas que possam ser respondidas com fragmentos do artigo. A saída deve ser uma lista de objetos JSON, com os atributos {{"pergunta": "Texto da pergunta Gerada", "resposta": "fragmento do artigo que responde a pergunta"}}. Não adicione nada na resposta, exceto a lista de objetos JSON, sem qualquer comentário adicional. ARTIGO: {}'''.format(artigo)
        payload = {
            "model": MODELO_OLLAMA,
            "prompt": prompt,
            "temperature": 0.0
        }
        resposta = requests.post(self.URL_OLLAMA, json=payload, stream=True)
        resposta.raise_for_status()
        texto_resposta = ''
        for fragmento in resposta.iter_content(chunk_size=None):
            if fragmento:
                dados = json.loads(fragmento.decode())
                texto_resposta += dados['response']
        return texto_resposta

    def run(self, url_arquivo_saida='documentos_perguntas.json', carregar_arquivo=False):
        if carregar_arquivo:
            print(f'Carregando {url_arquivo_saida}')
            with open(url_arquivo_saida, 'r', encoding='utf-8') as arq:
                documentos = json.load(arq)
        else:
            print(f'Consultando documentos do banco de vetores')
            client = chromadb.PersistentClient(path=self.URL_BANCO_VETORES)
            funcao_de_embeddings_sentence_tranformer = FuncaoEmbeddings(nome_modelo=self.NOME_MODELO, tipo_modelo=SentenceTransformer, device=self.DEVICE)
            collection = client.get_collection(name=self.NOME_COLECAO, embedding_function=funcao_de_embeddings_sentence_tranformer)
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
                perguntas = self.gerar_perguntas(artigo=doc['page_content'])
                doc['perguntas'] = perguntas
                
                with open(url_arquivo_saida, 'w', encoding='utf-8') as arq:
                    arq.write(json.dumps(documentos, indent=4, ensure_ascii=False))
                
if __name__ == "__main__":
    print('Iniciando gerador de perguntas')
    gerador_banco_perguntas = GeradorPerguntas()
    try:
        url_saida = sys.argv[1]
        gerador_banco_perguntas.run(url_arquivo_saida=url_saida, carregar_arquivo=True)
    except:
        gerador_banco_perguntas.run()
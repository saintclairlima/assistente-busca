## AFAZER: Ajustar para dar conta das alteraç~eos feitas nas classes usadas
import os
import chromadb
import requests
import json
import sys
from torch import cuda

from sentence_transformers import SentenceTransformer

from ..utils.interface_banco_vetores import FuncaoEmbeddings
from ..configuracoes.config_gerais import configuracoes
URL_LLM = 'http://localhost:11434/api/generate'
MODELO_LLM='llama3.1'
URL_LOCAL = os.path.abspath(os.path.join(os.path.dirname(__file__), "../dados"))
EMBEDDING_INSTRUCTOR="hkunlp/instructor-xl"
URL_BANCO_VETORES=os.path.join(URL_LOCAL,"bancos_vetores/banco_vetores_regimento_resolucoes_rh")
NOME_COLECAO='regimento_resolucoes_rh'
DEVICE='cuda' if cuda.is_available() else 'cpu'

class ValidadorPerguntas:
    def __init__(self,
                 url_llm=URL_LLM,
                 modelo_llm=MODELO_LLM,
                 url_local=URL_LOCAL,
                 nome_modelo=EMBEDDING_INSTRUCTOR,
                 device=DEVICE):
        self.URL_LLM = url_llm
        self.MODELO_LLM = modelo_llm
        self.URL_LOCAL = url_local
        self.NOME_MODELO = nome_modelo
        self.DEVICE = device

    def validar_pergunta(self, artigo, pergunta):
        prompt = f'''Considere este texto: {artigo}. Considere esta pergunta: {pergunta}. Analise a pergunta de forma criteriosa e crítica. Avalie se a pergunta é coerente e clara. Avalie se a pergunta pode ser respondida com base no texto. A saída deve ser um objeto JSON, com os atributos {{"coerente": true, "texto_responde": true}}. O atributo "coerente" deve ser true se a pergunta for clara e coerente. O atributo "texto_responde" deve ser true se a pergunta puder ser respondida com base no texto. Não adicione nada na resposta, exceto o objeto JSON, sem qualquer comentário adicional antes ou depois'''
        payload = {
            "model": MODELO_LLM,
            "prompt": prompt,
            "temperature": 0.0
        }
        resposta = requests.post(self.URL_LLM, json=payload, stream=True)
        resposta.raise_for_status()
        retorno = ''
        for fragmento in resposta.iter_content(chunk_size=None):
            if fragmento:
                dados = json.loads(fragmento.decode())
                retorno += dados['response']
        return retorno

    def run(self, url_arquivo='documentos_perguntas.json'):
        print(f'Carregando {url_arquivo}')
        with open(url_arquivo, 'r', encoding='utf-8') as arq:
            documentos = json.load(arq)

        qtd_docs = len(documentos)
        
        print(f'Validando perguntas para {qtd_docs} documentos')
        for idx in range(qtd_docs):
            print(f'\rProcessando documento {idx+1} de {qtd_docs}', end='')
            doc = documentos[idx]
            for pergunta in doc['perguntas']:
                if 'validacao' not in pergunta:
                    validacao = self.validar_pergunta(artigo=doc['page_content'], pergunta=pergunta)
                    pergunta['validacao'] = validacao
                    
                    with open(url_arquivo, 'w', encoding='utf-8') as arq:
                        arq.write(json.dumps(documentos, indent=4, ensure_ascii=False))
                
if __name__ == "__main__":
    print('Iniciando validador de perguntas')
    gerador_banco_perguntas = ValidadorPerguntas()
    try:
        url_saida = sys.argv[1]
        if url_saida: gerador_banco_perguntas.run(url_arquivo=url_saida)
        else: gerador_banco_perguntas.run()
    except:
        gerador_banco_perguntas.run()
## print('Para simplicidade, mover o arquivo para a pasta principal para executar')
print('Importando bibliotecas')
import argparse
import json
from time import time
from sentence_transformers import SentenceTransformer
from chromadb import chromadb
from ..configuracoes.config_gerais import configuracoes
from ..utils.utils import FuncaoEmbeddings, InterfaceOllama
import asyncio
import os
from torch import cuda
import sys

FAZER_LOG = False



URL_LOCAL = os.path.abspath(os.path.join(os.path.dirname(__file__), "./"))
URL_LLM = 'http://localhost:11434'
MODELO_OLLAMA='llama3.1'
EMBEDDING_INSTRUCTOR="hkunlp/instructor-xl"
URL_BANCO_VETORES=os.path.join(URL_LOCAL,"../dados/bancos_vetores/banco_vetores_regimento_resolucoes_rh")
NOME_COLECAO='regimento_resolucoes_rh'
DEVICE='cuda' if cuda.is_available() else 'cpu'

async def avaliar_respostas_ollama(url_arquivo_entrada, nome_banco_vetores, nome_colecao, url_arquivo_saida=None, instrucao=None):
    if not url_arquivo_saida: url_arquivo_saida = url_arquivo_entrada
    if FAZER_LOG: print('Carregando JSON')
    with open(url_arquivo_entrada, 'r', encoding='utf-8') as arq:
        dados = json.load(arq)
        dados=dados['dados'] # por motivodfe mudança na estrutura do arquivo
    if FAZER_LOG: print('Criando interface Ollama')
    interface_ollama = InterfaceOllama(url_ollama=URL_LLM, nome_modelo=MODELO_OLLAMA)

    if FAZER_LOG: print('Criando cliente Chroma')
    url_banco_vetores = os.path.join(URL_LOCAL, f"../dados/bancos_vetores/{nome_banco_vetores}")
    client = chromadb.PersistentClient(path=url_banco_vetores)
    if FAZER_LOG: print('Criando função de embeddings')
    funcao_de_embeddings_sentence_tranformer = FuncaoEmbeddings(nome_modelo=EMBEDDING_INSTRUCTOR, tipo_modelo=SentenceTransformer, instrucao=instrucao, device=DEVICE)
    if FAZER_LOG: print('Definindo Coleção')
    collection = client.get_collection(name=nome_colecao, embedding_function=funcao_de_embeddings_sentence_tranformer)
    
    if FAZER_LOG: print('Processando perguntas')
    num_itens = len(dados)
    for idx in range(num_itens):
        print(f'\rPergunta {idx+1} de {num_itens}', end="")
        item = dados[idx]

        # Ignora Cada item que já tem uma resposta do ollama
        if 'resp_llm' in item: continue

        pergunta = item['pergunta']
        if FAZER_LOG: print('Recuperando documentos')
        documentos = collection.get(
            ids=[doc['id'] for doc in item['documentos']]
        )
        if FAZER_LOG: print('Enviando dados para o ollama')
        texto_resposta_llm = ''
        async for resp_llm in interface_ollama.gerar_resposta_llm(
                    pergunta=pergunta,
                    # Inclui o título dos documentos no prompt do Ollama
                    documentos=[f"{doc[0]['titulo']} - {doc[1]}" for doc in zip(documentos['metadatas'], documentos['documents'])],
                    historico=[]):
            
            texto_resposta_llm += resp_llm['response']

        resp_llm['response'] = texto_resposta_llm
        resp_llm['context'] = []

        item['resp_llm'] = resp_llm

        if FAZER_LOG: print('salvando json')
        with open(os.path.join(url_arquivo_saida), 'w', encoding='utf-8') as arq:
            arq.write(json.dumps(dados, ensure_ascii=False, indent=4))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Gera resultados de busca por documentos a partir de uma lista de perguntas")

    parser.add_argument('--url_entrada', type=str, required=True, help="caminho para arquivo com as perguntas")
    parser.add_argument('--nome_banco_vetores', type=str, required=True, help="nome do banco de vetores a ser consultado")
    parser.add_argument('--nome_colecao', type=str, required=True, help="coleçaõ do banco a ser utilizada")
    parser.add_argument('--url_saida', type=str, help="caminho para arquivo em que serão salvos os resultados")
    parser.add_argument('--instrucao', type=str, help="instrucao a ser utilizada na função de embeddings")

    args = parser.parse_args()
    url_entrada = args.url_entrada
    nome_banco_vetores = args.nome_banco_vetores
    nome_colecao = args.nome_colecao
    url_saida = None if not args.url_saida else args.url_saida
    instrucao = None if not args.instrucao else args.instrucao
    asyncio.run(avaliar_respostas_ollama(
        url_arquivo_entrada=url_entrada,
        nome_banco_vetores=nome_banco_vetores,
        nome_colecao=nome_colecao,
        url_arquivo_saida=url_saida,
        instrucao=instrucao
    ))
# else:
#     avaliar_respostas_ollama(
#         url_arquivo_entrada=url_entrada,
#         nome_banco_vetores=nome_banco_vetores,
#         nome_colecao=nome_colecao,
#         url_arquivo_saida=url_saida,
#         instrucao=instrucao
#     )
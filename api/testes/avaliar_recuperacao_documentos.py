## print('Para simplicidade, mover o arquivo para a pasta principal para executar')
print('Importando bibliotecas...')
import json
import sys
from sentence_transformers import SentenceTransformer
from ..configuracoes.config_gerais import configuracoes
from ..gerador_de_respostas import GeradorDeRespostas
from ..utils.interface_banco_vetores import FuncaoEmbeddings
from time import time
import asyncio
import os
import argparse
from torch import cuda

URL_LOCAL = os.path.abspath(os.path.join(os.path.dirname(__file__), "./"))
EMBEDDING_INSTRUCTOR="hkunlp/instructor-xl"
DEVICE='cuda' if cuda.is_available() else 'cpu'

async def avaliar_recuperacao_documentos(
    url_arquivo_entrada,
    nome_banco_vetores,
    nome_colecao,
    url_arquivo_saida=None,
    instrucao=None,
    fazer_log=False):
    
    if not url_arquivo_saida: url_arquivo_saida = url_arquivo_entrada.split('.')[0] + '_recup_docs.json'
    url_banco_vetores = os.path.join(URL_LOCAL, f"../dados/bancos_vetores/{nome_banco_vetores}")
    print(f'Criando GeradorDeRespostas (usando {EMBEDDING_INSTRUCTOR} e instrução "{instrucao}")...')
    funcao_de_embeddings = FuncaoEmbeddings(nome_modelo=EMBEDDING_INSTRUCTOR, tipo_modelo=SentenceTransformer, device=DEVICE, instrucao=instrucao)
    gerador_de_respostas = GeradorDeRespostas(funcao_de_embeddings=funcao_de_embeddings, url_banco_vetores=url_banco_vetores, colecao_de_documentos=nome_colecao, device=DEVICE)

    with open(url_arquivo_entrada, 'r') as arq:
        docs = json.load(arq)
    
    print(f'Recuperando lista de documentos com perguntas ({url_arquivo_entrada})...')
    print(f'Os resultados serão salvos em {url_arquivo_saida}')
    perguntas = []
    for item in docs['dados']:
        for pergunta in item['perguntas']:
            try:
                if pergunta['resposta'] != '': perguntas.append({'id': item['id'], 'titulo': item['metadata']['titulo'], 'subtitulo': item['metadata']['subtitulo'], 'pergunta': pergunta['pergunta'], 'resposta': pergunta['resposta']})
            except:
                print(pergunta)

    qtd_perguntas = len(perguntas)
    for idx in range(qtd_perguntas):
        pergunta = perguntas[idx]
        print(f'\rPergunta {idx+1} de {qtd_perguntas}', end='')
        if fazer_log: print(f'''-- realizando consulta para: "{pergunta['pergunta']}"...''')

        # Recuperando documentos usando o ChromaDB
        marcador_tempo_inicio = time()
        documentos = await gerador_de_respostas.consultar_documentos_banco_vetores(pergunta['pergunta'], num_resultados=10)
        lista_documentos = gerador_de_respostas.formatar_lista_documentos(documentos)
        marcador_tempo_fim = time()
        tempo_consulta = marcador_tempo_fim - marcador_tempo_inicio
        if fazer_log: print(f'--- consulta no banco concluída ({tempo_consulta} segundos)')

        # Atribuindo scores usando Bert
        if fazer_log: print(f'--- aplicando scores do Bert aos documentos recuperados...')
        marcador_tempo_inicio = time()
        for documento in lista_documentos:
            resposta_estimada = await gerador_de_respostas.reclassificar_documentos(pergunta['pergunta'], documento['conteudo'])
            documento['score_bert'] = resposta_estimada['score']
            documento['score_ponderado'] = resposta_estimada['score_ponderado']
            documento['resposta_bert'] = resposta_estimada['resposta']
        marcador_tempo_fim = time()
        tempo_bert = marcador_tempo_fim - marcador_tempo_inicio
        if fazer_log: print(f'--- scores atribuídos ({tempo_bert} segundos)\n\n\n')
        pergunta.update({
            'documentos': [
                {'id': doc['id'],
                'titulo': doc['metadados']['titulo'],
                'subtitulo': doc['metadados']['subtitulo'],
                'score_bert': doc['score_bert'],
                'score_distancia': doc['score_distancia'],
                'score_ponderado': doc['score_ponderado'],
                'resposta_bert': doc['resposta_bert']
                } for doc in lista_documentos],
            'tempo_consulta': tempo_consulta,
            'tempo_bert': tempo_bert
            })


        with open(url_arquivo_saida, 'w', encoding='utf-8') as arq:
            json.dump(perguntas, arq, indent=4, ensure_ascii=False)



# Run the `avaliar` function
if __name__ == "__main__":
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
    asyncio.run(avaliar_recuperacao_documentos(
        url_arquivo_entrada=url_entrada,
        nome_banco_vetores=nome_banco_vetores,
        nome_colecao=nome_colecao,
        url_arquivo_saida=url_saida,
        instrucao=instrucao))

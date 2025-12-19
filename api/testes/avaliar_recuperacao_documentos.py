print('Carregando bibliotecas...')

import argparse
import json, os
from typing import Dict, List
from chromadb import chromadb
from torch import cuda

from dados.gerenciador_banco_vetores import GerenciadorBancoVetores
from api.utils.reclassificador import ReclassificadorBert
from api.configuracoes.config_gerais import configuracoes

DEVICE='cuda' if cuda.is_available() else 'cpu'
print(f'Ambiente de execução: {DEVICE}')


def recuperar_colecoes(url_banco_vetores: str) -> Dict[str, chromadb.Collection]:
    '''
    Recupera uma lista de chromadb.Collections correspondente às coleções em um banco de vetores.

    Parâmetros:
        url_banco_vetores (str): a url do banco de vetores

    Retorna:
        (Dict[str, chromadb.Collection]) as coleções existentes no banco de vetores
    '''

    with open(os.path.abspath(os.path.join(url_banco_vetores, 'descritor.json')), 'r') as arq:
        desc = json.load(arq)
    
    colecoes = {}
    cliente_chroma = chromadb.PersistentClient(path=url_banco_vetores)
    gb = GerenciadorBancoVetores()

    for desc_colecao in desc['colecoes']:
        funcao = gb.obter_funcao_embeddings(
            nome_modelo=desc_colecao['funcao_embeddings']['nome_modelo'],
            instrucao=desc_colecao['instrucao']
        )
        colecao = cliente_chroma.get_collection(name=desc_colecao['nome'], embedding_function=funcao)
        colecoes[desc_colecao['nome']] = colecao
    
    return colecoes

def gerar_mapa_fragmentos(fragmentos_referencia: List[dict], colecoes: Dict[str, chromadb.Collection]) -> dict:
    '''
    Recupera um dicionário em que a chave corresponde ao id de um documento de uma coleção e o valor é
    o id de um documento com conteúdo idêntico em uma lista de referência.

    Assume que todas as coleções têm somente documentos cujo conteúdo seja igual ao de um e somente um
    documento na lista de referência.
    É necessário, porque embora dois documentos que têm o mesmo conteúdo em coleções diferentes, seus uuids
    são distintos. Como o arquivo de referência, usado para criar as perguntas, é criado com base em uma das
    coleções, é necessário mapear os ids dos arquivos correspondentes das outras coleções com os do documento
    de referência.

    Parâmetros:
        fragmentos_referencia (List[dict]): a url do banco de vetores
        colecoes (Dict[str, chromadb.Collection]): coleções existentes no banco de vetores

    Retorna:
        (dict): mapeamento
    '''

    referencia = {fragmento['page_content']: fragmento['id'] for fragmento in fragmentos_referencia}
    grupo_documentos = [{conteudo: id for conteudo, id in zip(dados['documents'], dados['ids'])} for dados in (c.get() for c in colecoes.values())]
    mapa = {}
    for grupo in grupo_documentos:
        for conteudo, id in grupo.items():
            mapa[id] = referencia[conteudo]
    return mapa


def simular_recuperacao_documentos(url_arq_fragmentos: str, url_banco_vetores: str, num_resultados: int) -> List[dict]:
    '''
    Utiliza uma lista de perguntas geradas para fragmentos no banco vetorial e realiza recuperação de documentos por similaridade.

    Parâmetros:
        url_arq_fragmentos (str): a url do arquivo com fragmentos e perguntas
        url_banco_vetores (str): a url do banco de vetores
        num_resultados (int): a quantidade de documentos a serem recuperados do banco vetorial

    Retorna:
        (List[dict]): a url do banco de vetores

    **Observação:**
    Assume que o formato do arquivo com a lista de fragmentos e perguntas segue o que é retornado pelo método
    **`api.testes.gerador_perguntas.gerar_perguntas_banco_vetorial`**:

    ```python
    {
        "id": str,
        "page_content": str,
        "metadata": dict,
        "perguntas": [ { "pergunta": str, "trecho_resposta": str } ]
    }
    ```

    O valor retornado segue o seguinte formato:
    ```python
    [{
        'id_frag': str,
        'pergunta': str,
        'docs_recuperados': [{
            'nome_colecao': str,
            'documentos': [{
                'id': str,
                'score_bert': { 'resposta': str, 'score': (float, float), 'score_ponderado': float },
                'score_cosseno': float
            }]
        }]
    }]
    ```
    '''
    
    colecoes = recuperar_colecoes(url_banco_vetores=url_banco_vetores)
    with open(url_arq_fragmentos, 'r', encoding='utf-8') as arq:
        fragmentos_com_perguntas = json.load(arq)

    reclassificador_bert = ReclassificadorBert(device=DEVICE, fazer_log=False)
    mapa_fragmentos = gerar_mapa_fragmentos(fragmentos_referencia=fragmentos_com_perguntas, colecoes=colecoes)

    resultado = []
    for idx in range(len(fragmentos_com_perguntas)):
        fragmento = fragmentos_com_perguntas[idx]
        id_frag = fragmento['id']
        perguntas = [par['pergunta'] for par in fragmento['perguntas']]
        print('RECUPERANDO DOCUMENTOS')
        print(f'Processando fragmento {idx+1} de {len(fragmentos_com_perguntas)}')

        for idx in range(len(perguntas)):
            print(f'-- pergunta {idx+1} de {len(perguntas)}')
            pergunta = perguntas[idx]
            relat_busca = {
                'id_frag': id_frag,
                'pergunta': pergunta,
                'docs_recuperados': []
            }

            for nome_colecao, colecao in colecoes.items():
                print(f'--- recuperando da colecao {nome_colecao}...')
                res_consulta = colecao.query(query_texts=[pergunta], n_results=num_resultados)
                ids = res_consulta['ids'][0]
                conteudo = res_consulta['documents'][0]
                distancias = res_consulta['distances'][0]
                documentos = [item for item in zip(ids, conteudo, distancias)]
                documentos = [{
                    'id': mapa_fragmentos[doc[0]],
                    'score_bert': reclassificador_bert.reclassificar_documento(pergunta=pergunta, texto_documento=doc[1]),
                    'score_cosseno': doc[2]
                } for doc in documentos]

                relat_busca['docs_recuperados'].append(
                    {
                        'nome_colecao': nome_colecao,
                        'documentos': documentos
                    }
                )
            
            resultado.append(relat_busca)
    return resultado

def avaliar_recuperacao(
    url_arq_fragmentos: str,
    url_banco_vetores: str,
    url_arquivo_saida: str,
    num_resultados: int,
    gerar_relatorios_intermediarios_avaliacao: bool=False) -> List[dict]:

    '''
    Utiliza uma lista de perguntas geradas para fragmentos no banco vetorial e realiza uma análise comparativa da taxa de recuperação
    de documentos por coleção/modelo de embeddings em um banco vetorial.

    Parâmetros:
        url_arq_fragmentos (str): url do arquivo com fragmentos e perguntas a ser utilizado para realizar consultas
        url_banco_vetores (str): url do banco de vetores
        url_arquivo_saida (str): caminho onde salvar o arquivo de saída
        num_resultados (int): número de resultados de cada consulta ao banco de vetores
        gerar_relatorios_intermediarios_avaliacao (bool) OPCIONAL. Default: False
    
    Retorna:
        (List[dict]): lista com relatório de cada uma das coleções.

    O retorno segue o seguinte formato:
    ```python
        [{
            nome_colecao: {
                'lista_ranking_documento_original': [ item (int)],
                'lista_score_cosseno': [ item (float)],
                'lista_score_bert_estimado': [ item (float)],
                'lista_score_bert_soma': [ item (float)],
                'lista_score_bert_ponderado': [ item (float)],
                'posicao_media_distribuicao': {chave (int) : valor (int)},
                'posicao_media': valor (float),
                'score_cosseno_media': valor (float),
                'score_bert_estimado_media': valor (float),
                'score_bert_soma_media': valor (float),
                'posicao_mscore_bert_ponderado_mediaedia': valor (float),
            }
        }]
    ```
    '''

    # obtém resultados de consultas no banco vetorial
    simulacao_recuperacao = simular_recuperacao_documentos(url_arq_fragmentos=url_arq_fragmentos, url_banco_vetores=url_banco_vetores, num_resultados=num_resultados)

    # salva os resultados da busca
    if gerar_relatorios_intermediarios_avaliacao:
        with open(url_arq_fragmentos[:-5] + '_simulacao_recuperacao.json', 'w', encoding='utf-8') as arq:
            json.dump(simulacao_recuperacao, arq, ensure_ascii=False, indent=4)

    resultados_detalhados = []
    # Realiza cálculo de resultados intermediários
    for item_pergunta in simulacao_recuperacao:
        id_frag = item_pergunta['id_frag']
        pergunta = item_pergunta['pergunta']
        for resultados_colecao in item_pergunta['docs_recuperados']:
            colecao = resultados_colecao['nome_colecao']
            ids_docs = [doc['id'] for doc in resultados_colecao['documentos']]
            if id_frag in ids_docs:
                posicao = ids_docs.index(id_frag)
                score_cosseno = resultados_colecao['documentos'][posicao]['score_cosseno']
                score_bert_estimado = resultados_colecao['documentos'][posicao]['score_bert']['score'][0]
                score_bert_soma = resultados_colecao['documentos'][posicao]['score_bert']['score'][1]
                score_bert_ponderado = resultados_colecao['documentos'][posicao]['score_bert']['score_ponderado']
            else:
                posicao = None
                score_cosseno = None
                score_bert_estimado = None
                score_bert_soma = None
                score_bert_ponderado = None

            resultados_detalhados.append({
                'id_frag': id_frag,
                'pergunta': pergunta,
                'colecao': colecao,
                'posicao': posicao,
                'score_cosseno': score_cosseno,
                'score_bert_estimado': score_bert_estimado,
                'score_bert_soma': score_bert_soma,
                'score_bert_ponderado': score_bert_ponderado
            })

    # salva resultados intermediários
    if gerar_relatorios_intermediarios_avaliacao:
        with open(url_arq_fragmentos[:-5] + '_avaliacao_resultados_detalhados.json', 'w', encoding='utf-8') as arq:
            json.dump(resultados_detalhados, arq, ensure_ascii=False, indent=4)
    
    sumario_resultados = {
        nome_colecao: {
            'lista_ranking_documento_original': [],
            'lista_score_cosseno': [],
            'lista_score_bert_estimado': [],
            'lista_score_bert_soma': [],
            'lista_score_bert_ponderado': []
        } for nome_colecao in set([item['colecao'] for item in resultados_detalhados])
    }

    # sumariza resultados
    for item in resultados_detalhados:
        sumario_resultados[item['colecao']]['lista_ranking_documento_original'].append(item['posicao'])
        sumario_resultados[item['colecao']]['lista_score_cosseno'].append(item['score_cosseno'])
        sumario_resultados[item['colecao']]['lista_score_bert_estimado'].append(item['score_bert_estimado'])
        sumario_resultados[item['colecao']]['lista_score_bert_soma'].append(item['score_bert_soma'])
        sumario_resultados[item['colecao']]['lista_score_bert_ponderado'].append(item['score_bert_ponderado'])

    for colecao, resultados in sumario_resultados.items():
        resultados['posicao_media_distribuicao'] = {posicao: resultados['lista_ranking_documento_original'].count(posicao) for posicao in [idx for idx in range(10)] + [None]}
        resultados['posicao_media'] = sum(filter(None, resultados['lista_ranking_documento_original'])) / len([item for item in filter(None, resultados['lista_ranking_documento_original'])])
        resultados['score_cosseno_media'] = sum(filter(None, resultados['lista_score_cosseno'])) / len([item for item in filter(None, resultados['lista_score_cosseno'])])
        resultados['score_bert_estimado_media'] = sum(filter(None, resultados['lista_score_bert_estimado'])) / len([item for item in filter(None, resultados['lista_score_bert_estimado'])])
        resultados['score_bert_soma_media'] = sum(filter(None, resultados['lista_score_bert_soma'])) / len([item for item in filter(None, resultados['lista_score_bert_soma'])])
        resultados['score_bert_ponderado_media'] = sum(filter(None, resultados['lista_score_bert_ponderado'])) / len([item for item in filter(None, resultados['lista_score_bert_ponderado'])])

        
    # salva resultado final, sumarizado
    with open(url_arquivo_saida, 'w', encoding='utf-8') as arq:
        json.dump(sumario_resultados, arq, ensure_ascii=False, indent=4)

    # imprime sumário em tela
    print('SUMÁRIO DOS RESULTADOS')

    for colecao, resultados in sumario_resultados.items():
        print(f'''
    ==== {colecao} ====
    Posicao: {resultados['posicao_media']}
    Cosseno:{resultados['score_cosseno_media']}
    Bert Estimado: {resultados['score_bert_estimado_media']}
    Bert Soma: {resultados['score_bert_soma_media']}
    Bert Ponderado: {resultados['score_bert_ponderado_media']}


    ''')
        
    for colecao, resultados in sumario_resultados.items():
        print(f'======={colecao}=========')
        for pos, cont in resultados['posicao_media_distribuicao'].items():
            print(f'{pos}\t{cont}')
        print('\n')

    return resultados_detalhados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera resultados de busca por documentos a partir de uma lista de perguntas")
    parser.add_argument('--url_arq_fragmentos', type=str, help="caminho para arquivo com as perguntas")
    parser.add_argument('--url_banco_vetores', type=str, help="nome do banco de vetores a ser consultado")
    parser.add_argument('--url_arquivo_saida', type=str, help="caminho para salvar o arquivo com o resultado")
    parser.add_argument('--num_resultados', type=int, help='quantidade de documentos a ser recuperada de cada consulta ao banco de vetores')
    parser.add_argument('--gerar_relatorios_intermediarios', type=bool, help='indicador se deve ou não salvar os resultados')
    args = parser.parse_args()

    url_arq_fragmentos = 'api/testes/resultados/perguntas_documentos.json' if not args.url_arq_fragmentos else args.url_arq_fragmentos
    url_banco_vetores = configuracoes.url_banco_vetores if not args.url_banco_vetores else args.url_banco_vetores
    url_arquivo_saida = os.path.basename(url_arq_fragmentos)[:-5] + '_sumario.json' if not args.url_arquivo_saida else args.url_arquivo_saida
    num_resultados = 10 if not args.num_resultados else args.num_resultados
    gerar_relatorios_intermediarios = True if not args.num_resultados else args.num_resultados

    res = avaliar_recuperacao(
        url_arq_fragmentos = url_arq_fragmentos,
        url_banco_vetores = url_banco_vetores,
        url_arquivo_saida = url_arquivo_saida,
        num_resultados = num_resultados,
        gerar_relatorios_intermediarios_avaliacao = gerar_relatorios_intermediarios
    )

# Modelo de execução
# !python -m api.testes.avaliar_recuperacao_documentos \
# --url_arq_fragmentos api/testes/resultados/perguntas_documentos.json \
# --url_banco_vetores api/dados/bancos_vetores/banco_assistente \
# --url_arquivo_saida api/testes/resultados/perguntas_documentos_sumario.json\
# --num_resultados 10 \
# --gerar_relatorios_intermediarios True
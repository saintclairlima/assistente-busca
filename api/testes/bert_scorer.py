print('Fazendo imports...')
import argparse
import json
from bert_score import score

def aplicar_score(url_arquivo_entrada, url_arquivo_saida=None):
    if not url_arquivo_saida: url_arquivo_saida = url_arquivo_entrada.split('.')[0] + '_bertscore.json'
    
    print(f'Carregando dados({url_arquivo_entrada})...')
    with open(url_arquivo_entrada, 'r') as arq:
        dados = json.load(arq)
        dados = dados['dados']

    candidates = []
    references = []
    indices = []

    for idx in range(len(dados)):
        item = dados[idx]
        if 'resp_llm' in item:
            indices.append(idx)
            candidates.append(item['resposta'])
            references.append(item['resp_llm']['response'])

    print('Calculando BertScore...')
    P, R, F1 = score(candidates, references, lang="pt-br", verbose=False)

    resultado = [
        {
            'indice': indices[i],
            'precision': P[i].item(),
            'recall': R[i].item(),
            'f1': F1[i].item()
        } for i in range(len(candidates))]
    
    with open(url_arquivo_saida, 'w', encoding='utf-8') as arq:
        json.dump(resultado, arq, ensure_ascii=False, indent=4)
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Gera resultados de busca por documentos a partir de uma lista de perguntas")
    
    parser.add_argument('--url_entrada', type=str, required=True, help="caminho para arquivo com as perguntas")
    parser.add_argument('--url_saida', type=str, help="caminho para arquivo em que serão salvos os resultados")
    
    args = parser.parse_args()
    url_entrada = args.url_entrada
    url_saida = None if not args.url_saida else args.url_saida
    
    aplicar_score(url_arquivo_entrada=url_entrada, url_arquivo_saida=url_saida)
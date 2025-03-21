print('Carregando bibliotecas...')
import argparse
import ast
import json
from typing import List
from bert_score import score
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def aplicar_score(textos_candidatos, textos_referencia):
    indices = [idx for idx in range(len(textos_candidatos))]

    print('Calculando BertScore...')
    P, R, F1 = score(textos_candidatos, textos_referencia, lang="pt-br", verbose=False)
    
    resultado = [
        {
            'indice': indices[i],
            'precision': P[i].item(),
            'recall': R[i].item(),
            'f1': F1[i].item()
        } for i in range(len(textos_candidatos))]
    
    return resultado

def avaliar_respostas_llm(dados: List[dict], modelos_llm: List[str]) -> dict:

    respostas = {'referencia': []}
    for modelo in modelos_llm:
        respostas[modelo] = []

    for item in dados:
        todos_modelos = True

        for modelo in modelos_llm:
            if modelo not in item:
                todos_modelos = False
                break

        if todos_modelos:
            respostas['referencia'].append(item['resposta'])
            for modelo in modelos_llm:
                if modelo != 'resposta_gpt-4o':
                    if '<think>' in item[modelo]['message']['content'] and '<think/>' in item[modelo]['message']['content']:
                        item[modelo]['message']['content'] = item[modelo]['message']['content'].split('</think>')[1]
                    respostas[modelo].append(item[modelo]['message']['content'])
                else:
                    respostas[modelo].append(item[modelo]["choices"][0]["message"]["content"])
    
    scores = {
        modelo: aplicar_score(respostas[modelo], respostas['referencia']) for modelo in modelos_llm
    }

    return scores
        
        
# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description="Gera resultados de busca por documentos a partir de uma lista de perguntas")
    
#     parser.add_argument('--url_entrada', type=str, help="caminho para arquivo com as perguntas")
#     parser.add_argument('--url_saida', type=str, help="caminho para arquivo em que serão salvos os resultados")
#     parser.add_argument('--modelos_llm', type=str, help="lista de modelos testados")    
#     args = parser.parse_args()

#     url_entrada = 'api/testes/resultados/perguntas_documentos_rh_simulacao_perguntas.json' if not args.url_entrada else args.url_entrada
#     url_saida = url_entrada[:-5] + '_bertscore.json' if not args.url_saida else args.url_saida
#     modelos_llm = ast.literal_eval(f'["resposta_deepseek-r1:latest", "resposta_llama3.1", "resposta_gpt-4o"]') if not args.modelos_llm else ast.literal_eval(args.modelos_llm)
#     with open(url_entrada, 'r', encoding='utf-8') as arq:
#         dados = json.load(arq)
    
#     scores_modelos = avaliar_respostas_llm(dados=dados, modelos_llm=modelos_llm)

#     with open(url_saida, 'w', encoding='utf-8') as arq:
#         json.dump(scores_modelos, arq)

#     for modelo, lista_scores in scores_modelos.items():
#         scores_detalhados = {
#             "precision": [],
#             "recall": [],
#             "f1": []
#         }

#         for score in lista_scores:
#             scores_detalhados['precision'].append(score['precision'])
#             scores_detalhados['recall'].append(score['recall'])
#             scores_detalhados['f1'].append(score['f1'])
        
#         scores_medias = {
#             "precision": sum(scores_detalhados['precision']) / len(scores_detalhados['precision']),
#             "recall": sum(scores_detalhados['recall']) / len(scores_detalhados['recall']),
#             "f1": sum(scores_detalhados['f1']) / len(scores_detalhados['f1']),
#         }

#         print(f'=== Relatório de Scores - {modelo} ===')
#         for score, valor in scores_medias.items():
#             print(f'- {score}:\t{valor}')
#         print('--------------------------\n\n')



def plotar_resultados(url_arquivo: str='api/testes/resultados/perguntas_documentos_rh_simulacao_perguntas_bertscore.json'):
    with open(url_arquivo, 'r', encoding='utf-8') as arq:
        dados = json.load(arq)
        
    scores_llama = {"precision": [], "recall": [], "f1": []}
    for score in dados['resposta_llama3.1']:
        scores_llama['precision'].append(score['precision'])
        scores_llama['recall'].append(score['recall'])
        scores_llama['f1'].append(score['f1'])

    scores_deepseek = {"precision": [], "recall": [], "f1": []}
    for score in dados['resposta_deepseek-r1:latest']:
        scores_deepseek['precision'].append(score['precision'])
        scores_deepseek['recall'].append(score['recall'])
        scores_deepseek['f1'].append(score['f1'])
        
    scores_gpt = {"precision": [], "recall": [], "f1": []}
    for score in dados['resposta_gpt-4o']:
        scores_gpt['precision'].append(score['precision'])
        scores_gpt['recall'].append(score['recall'])
        scores_gpt['f1'].append(score['f1'])
        
    def dict_to_df(scores_dict, label):
        df = pd.DataFrame(scores_dict)
        df = df.melt(var_name="Métrica", value_name="Score")
        df["Modelo"] = label
        return df

    df_llama = dict_to_df(scores_llama, "llama3.1")
    df_deepseek = dict_to_df(scores_deepseek, "deepseek-r1")
    df_gpt = dict_to_df(scores_gpt, "gpt-4o")
    
    combined_df = pd.concat([df_llama, df_deepseek, df_gpt], ignore_index=True)
    
    sns.set(style="white", font_scale=1.1)
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

    colors = {
        "llama3.1": "#aec7e8",
        "deepseek-r1": "#ffbb78",
        "gpt-4o": "#c1e1c1"
    }

    metrics = ["precision", "recall", "f1"]

    for i, metric in enumerate(metrics):
        ax = axes[i]
        metric_data = combined_df[combined_df["Métrica"] == metric]
        
        sns.boxplot(
            x="Modelo", y="Score",
            data=metric_data,
            ax=ax,
            palette=colors,
            width=0.6,
            boxprops=dict(alpha=0.8)
        )
        
        ax.set_title(metric.upper(), fontsize=14)
        ax.set_xlabel("")  # remove xlabel
        if i == 0:
            ax.set_ylabel("Score")
        else:
            ax.set_ylabel("")
        
        # Clean aesthetics: remove vertical lines
        ax.grid(axis='y', linewidth=0.3)
        ax.set_axisbelow(True)

    fig.suptitle("Comparativo de BERTScore por Métrica", fontsize=16)
    plt.tight_layout()
    plt.show()

plotar_resultados()

print('Carregando bibliotecas...')
import argparse
import ast
import json
from openai import OpenAI
from time import time
from typing import List
from api.configuracoes.config_gerais import configuracoes
from api.utils.gerador_prompts import GeradorPrompts

def simular_geracao_resposta_openai(
        pergunta:str,
        documentos: List[str],
        modelo_llm: str=configuracoes.modelo_llm):
    
    prompt_usuario = GeradorPrompts.gerar_prompt_rag(pergunta=pergunta, documentos=documentos)

    mensagens = [
        {'role': 'system', 'content': configuracoes.template_mensagem_system},
        {'role': 'user', 'content': prompt_usuario}
    ]
    
    cliente_openai = OpenAI()

    tempo_inicial = time()
    resultado = cliente_openai.chat.completions.create(
            model=modelo_llm,
            messages=mensagens
        )
    resultado = json.loads(resultado.model_dump_json())
    resultado['tempo_execucao'] = time() - tempo_inicial

    return resultado

def avaliar_respostas_openai(url_arquivo_perguntas: str, modelo_llm: str):

    with open(url_arquivo_perguntas, 'r', encoding='utf-8') as arq:
        info_perguntas = json.load(arq)

    qtd_perguntas = len(info_perguntas)
    
    for idx in range(qtd_perguntas):
        item = info_perguntas[idx]
        if 'resposta_' + modelo_llm not in item:
            print(f'\r--- processando pergunta {idx+1} de {qtd_perguntas}...', end='')
            pergunta = item['pergunta']
            documentos = item['docs']
            resposta = simular_geracao_resposta_openai(
                pergunta=pergunta,
                documentos=documentos,
                modelo_llm=modelo_llm)
            
            item['resposta_' + modelo_llm] = resposta

            with open(url_arquivo_perguntas, 'w', encoding='utf-8') as arq:
                json.dump(info_perguntas, arq, ensure_ascii=False, indent=4)
    
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera respostas da API da OpenAI a partir de uma lista de perguntas")
    parser.add_argument('--url_arquivo_perguntas', type=str, help="caminho para arquivo com as perguntas e documentos")
    parser.add_argument('--modelos_llm', type=str, help='lista de modelos a serem testados')
    args = parser.parse_args()

    url_arquivo_perguntas = 'api/testes/resultados/perguntas_documentos_rh_simulacao_perguntas.json' if not args.url_arquivo_perguntas else args.url_arquivo_perguntas
    modelos_llm = ast.literal_eval(f'["gpt-4o"]') if not args.modelos_llm else ast.literal_eval(args.modelos_llm)

    print(f'Respostas sendo enviadas à API OpenAI...')
    for modelo in modelos_llm:
        print(f'\nGerando respostas com {modelo}:')
        avaliar_respostas_openai(url_arquivo_perguntas=url_arquivo_perguntas, modelo_llm=modelo)

    print('\nConcluído!!!')
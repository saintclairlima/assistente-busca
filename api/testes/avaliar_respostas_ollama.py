
print('Carregando bibliotecas...')
import argparse
import ast
import json
import requests
from time import time
from typing import List
from api.configuracoes.config_gerais import configuracoes
from api.utils.gerador_prompts import GeradorPrompts

def simular_geracao_resposta_ollama(
        pergunta:str,
        documentos: List[str],
        url_llm: str=configuracoes.url_llm,
        modelo_llm: str=configuracoes.modelo_llm):
    
    prompt_usuario = GeradorPrompts.gerar_prompt_rag(pergunta=pergunta, documentos=documentos)

    mensagens = [
        {'role': 'system', 'content': configuracoes.template_mensagem_system},
        {'role': 'user', 'content': prompt_usuario}
    ]

    payload = {
        "model": modelo_llm,
        "messages": mensagens,
        "temperature": 0.0,
        "stream": False
    }

    url = f"{url_llm}/api/chat"

    tempo_inicial = time()
    resultado = requests.post(url, json=payload)

    resposta_ollama = json.loads(resultado.content)
    resposta_ollama['tempo_execucao'] = time() - tempo_inicial

    return resposta_ollama

def avaliar_respostas_ollama(url_arquivo_perguntas: str, url_llm: str, modelo_llm: str):

    with open(url_arquivo_perguntas, 'r', encoding='utf-8') as arq:
        info_perguntas = json.load(arq)

    qtd_perguntas = len(info_perguntas)
    
    for idx in range(qtd_perguntas):
        item = info_perguntas[idx]
        if 'resposta_' + modelo_llm not in item:
            print(f'\r--- processando pergunta {idx+1} de {qtd_perguntas}...', end='')
            pergunta = item['pergunta']
            documentos = item['docs']
            resposta = simular_geracao_resposta_ollama(pergunta, documentos, url_llm, modelo_llm)
            item['resposta_' + modelo_llm] = resposta

            with open(url_arquivo_perguntas, 'w', encoding='utf-8') as arq:
                json.dump(info_perguntas, arq, ensure_ascii=False, indent=4)
    
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera respostas do Ollama a partir de uma lista de perguntas")
    parser.add_argument('--url_arquivo_perguntas', type=str, help="caminho para arquivo com as perguntas e documentos")
    parser.add_argument('--url_llm', type=str, help='url em que está sendo executado o LLM')
    parser.add_argument('--modelos_llm', type=str, help='lista de modelos a serem testados')
    args = parser.parse_args()

    url_arquivo_perguntas = 'api/testes/resultados/perguntas_documentos_rh_simulacao_perguntas.json' if not args.url_arquivo_perguntas else args.url_arquivo_perguntas
    url_llm = configuracoes.url_llm if not args.url_llm else args.url_llm
    modelos_llm = ast.literal_eval(f'["{configuracoes.modelo_llm}"]') if not args.modelos_llm else ast.literal_eval(args.modelos_llm)

    print(f'Respostas sendo enviadas a {url_llm}')
    for modelo in modelos_llm:
        print(f'\nGerando respostas com {modelo}:')
        avaliar_respostas_ollama(url_arquivo_perguntas=url_arquivo_perguntas, url_llm=url_llm, modelo_llm=modelo)

    print('\nConcluído!!!')
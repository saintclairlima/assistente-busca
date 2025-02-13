## AFAZER: Ajustar para dar conta das alteraç~eos feitas nas classes usadas
import json
import sys
from openai import OpenAI

class GeradorPerguntasOpenAI:
    def __init__(self, nome_modelo='gpt-4o', papel=None):
        self.cliente_openai = OpenAI()
        self.nome_modelo = nome_modelo
        
        if papel: self.papel = papel
        else:
            self.papel = '''
            Você é um gerador de perguntas sobre partes de textos legislativos. Quando recebe um texto,
            você cria pelo menos 5 perguntas que possam ser respondidas com fragmentos do texto recebido.
            Nos casos de Artigos revogados, retorne uma lista vazia: [].
            A saída deve ser uma lista de objetos JSON, com os atributos {{"pergunta": "Texto da pergunta Gerada", "resposta": "fragmento do artigo que responde a pergunta"}}.
            Não adicione nada na resposta, exceto a lista de objetos JSON, sem qualquer comentário adicional.
            '''
    
    def gerar_perguntas(self, texto) :
        return self.cliente_openai.chat.completions.create(
            model = self.nome_modelo,
            messages=[
                {"role": "system", "content": self.papel},
                {"role": "user",   "content": texto}
            ]
        )
    
    def run(self, url_arquivo_entrada, url_arquivo_saida=None):
        if not url_arquivo_saida: url_arquivo_saida = url_arquivo_entrada.split('.')[0] + '_perguntas.json'
        
        with open(url_arquivo_entrada, 'r') as arq:
            artigos = json.load(arq)
        
        arts_perguntas = {}
        
        for id, texto in artigos.items():
            print(f'\rProcessando documento de id {id}', end='')
            perguntas = self.gerar_perguntas(texto)
            
            arts_perguntas[id] = {
                'id': id,
                'texto': texto,
                'perguntas': perguntas.choices[0].message.content
            }
            
            with open(url_arquivo_saida, 'w', encoding='utf-8') as arq:
                json.dump(arts_perguntas, arq, ensure_ascii=False, indent=4)
                
if __name__ == "__main__":
    print('Iniciando gerador de perguntas')
    gerador_perguntas = GeradorPerguntasOpenAI()
    try:
        url_entrada = sys.argv[1]
        url_saida = sys.argv[2]
        gerador_perguntas.run(url_arquivo_entrada=url_entrada, url_arquivo_saida=url_saida)
    except:
        url_entrada = sys.argv[1]
        gerador_perguntas.run(url_arquivo_entrada=url_entrada)
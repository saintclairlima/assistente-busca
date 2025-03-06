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
            Você auxilia o setor de informações da Assembleia Legislativa do Rio Grande do Norte
            a responder perguntas dos servidores e cidadãos sobre a Assembleia. Sua função é
            ajudar a criar um banco de dados sintético com perguntas frequentes e dúvidas que
            servidores reais do serviço público poderiam ter. Esse banco de dados será usado para
            treinar uma aplicação que vai responder perguntas reais de servidores, portanto deve
            ter perguntas pertinentes e o mais próximo possível de dúvidas reais relacionadas aos
            temas de regulação de uma Assembleia Legislativa.
            '''
    
    def gerar_perguntas(self, texto) :
        prompt = f'''
        Você vai considerar um texto base, que é um artigo de uma lei. Após isso, extraia as informações do artigo e
        gere perguntas que possam ser respondidas com base no conteúdo textual do artigo. Além disso, formule a
        resposta com base no artigo e em nenhuma outra fonte. As perguntas e respostas serão utilizadas para
        treinamento e finetuning de um LLM. Siga as seguintes diretrizes para gerar as perguntas e respostas:

        Considere o texto recebido e identifique informações significativas;
        Com base nas informações, crie pelo menos 3 perguntas que possam ser respondidas com base no conteúdo do texto;
        Caso o texto fornecido não tenha informação a partir da qual seja possível criar perguntas relevantes, deve ser retornado um objeto vazio;
        As perguntas devem ser claras, diretas, e específicas;
        As perguntas podem ter sinônimos ou termos aproximados do texto base, mas devem ser possível de ser respondidas pelo texto fornecido;
        Para cada pergunta, formule uma resposta usando como base o conteúdo do artigo, sem utilizar qualquer outro conhecimento que você disponha.

        Cada pergunta será aceitável somente se:

        * Estiver relacionada aos assuntos pertinentes ao artigo apresentado
        * For uma pergunta relevante, semelhante ao que seria perguntado por uma pessoa vim dúvida
        * Puder ser respondida usando o fragmento apresentado

        O resultado deve ser uma lista de objetos JSON, com os atributos {[{"pergunta": "Texto da pergunta Gerada", "resposta": "fragmento do artigo que responde a pergunta"}]}.
        Não adicione nenhum texto adicional à resposta, exceto a lista de objetos JSON
        Um exemplo de como devem ser geradas as perguntas:

        Exemplo de texto base:
        "Art. 1º A Assembleia Legislativa é composta de Deputados, representantes do povo norte-rio-grandense, eleitos, na forma da lei, para mandato de 4 (quatro) anos."

        Resultado aceitável:
            {[
                {
                    "pergunta": "A Assembleia Legislativa é formada pelo que?",
                    "resposta": "A Assembleia Legislativa é composta por Deputados, que são eleitos pelo do povo norte-rio-grandense e os representam.",
                },
                {
                    "pergunta": "O que é um Deputado?",
                    "resposta": "Um Deputado é um representante eleito do povo, possuindo mandato de quatro anos.",
                },
                {
                    "pergunta": "Quanto tempo dura um mandato?",
                    "resposta": "Um mandato dura pelo período de quatro anos.",
                }
            ]}

        Caso o texto não tenha conteúdo relevante, o resultado deve ser um objeto vazio {{}}.
        ESTE É O TEXTO BASE: {texto}
        Vamos começar?'''
        
        return self.cliente_openai.chat.completions.create(
            model = self.nome_modelo,
            messages=[
                {"role": "system", "content": self.papel},
                {"role": "user",   "content": prompt}
            ],
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
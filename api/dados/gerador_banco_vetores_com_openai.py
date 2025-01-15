import argparse
import json
import os
from ..configuracoes.config_gerais import configuracoes
from ..utils.utils import FuncaoEmbeddings
from torch import cuda

from sentence_transformers import SentenceTransformer
from chromadb import chromadb
from pypdf import PdfReader
from bs4 import BeautifulSoup

import chromadb.utils.embedding_functions as embedding_functions

URL_LOCAL = os.path.abspath(os.path.join(os.path.dirname(__file__), "./"))
EMBEDDING_INSTRUCTOR="hkunlp/instructor-xl"
DEVICE='cuda' if cuda.is_available() else 'cpu'

# Valores padrão, geralmente não usados
NOME_BANCO_VETORES=os.path.join(URL_LOCAL,"bancos_vetores/banco_teste_default")
NOME_COLECAO='colecao_teste_default'
COMPRIMENTO_MAX_FRAGMENTO = 300    

class GeradorBancoVetores:
    
    def processar_texto_articulado(self, texto, info, comprimento_max_fragmento):
        '''Processa textos legais, divididos em artigos. Mantém o Caput dos artigos em cada um dos fragmentos.'''
        
        texto = texto.replace('\n', ' ')
        while '  ' in texto: texto = texto.replace('  ', ' ')
        texto = texto.replace(' Art. ', '\nArt. ')
        
        for num in range(1, 10):
                texto = texto.replace(f'Art. {num}º', f'Art. {num}.')
                texto = texto.replace(f'art. {num}º', f'art. {num}.')
                texto = texto.replace(f'§ {num}º', f'§ {num}.')
                
        texto = texto.split('\n')
        while '' in texto: texto.remove('')
        
        artigos = []
        for art in texto:
            item = art.split(' ')
            qtd_palavras = len(item)
            if qtd_palavras > comprimento_max_fragmento:
                item = (
                        art.replace('. §', '.\n§')
                        .replace('; §', ';\n§')
                        .replace(': §', ':\n§')
                        .replace(';', '\n')
                        .replace(':', '\n')
                        .replace('\n ', '\n')
                        .replace(' \n', '\n')
                        .split('\n')
                    )
                caput = item[0]
                fragmento_artigo = '' + caput
                # AFAZER: considerar casos em que, mesmo após divisão das
                # partes do artigo, haja alguma com mais palavras que o compr. máximo
                for i in range(1, len(item)):
                    if len(fragmento_artigo.split(' ')) + len(item[i].split(' ')) <= comprimento_max_fragmento:
                        fragmento_artigo = fragmento_artigo + ' ' + item[i]
                    else:
                        artigos.append(fragmento_artigo)
                        fragmento_artigo = '' + caput + ' ' + item[i]
                artigos.append(fragmento_artigo)
            else:
                artigos.append(art)
        
        fragmentos = []
        titulos = []
        for artigo in artigos:
            tit = artigo.split('. ')[1]
            titulos.append(tit)
            fragmento = {
                'page_content': artigo,
                'metadata': {
                    'titulo': f'{info["titulo"]}',
                    'subtitulo': f'Art. {tit} - {titulos.count(tit)}',
                    'autor': f'{info["autor"]}',
                    'fonte': f'{info["fonte"]}'
                },
            }
            fragmentos.append(fragmento)
        return fragmentos
    
    def processar_texto(self, texto, info, comprimento_max_fragmento, pagina=None):
        texto = texto.replace('\n', ' ').replace('\t', ' ')
        while '  ' in texto: texto = texto.replace('  ', ' ')
        
        if info['texto_articulado']:
            return self.processar_texto_articulado(texto, info, comprimento_max_fragmento)
        
        if len(texto.split(' ')) <= comprimento_max_fragmento:
            fragmento = {
                'page_content': texto,
                'metadata': {
                    'titulo': f'{info["titulo"]}',
                    'subtitulo':
                        f'Página {pagina} - Fragmento 1' if pagina
                        else f'Fragmento 1',
                    'autor': f'{info["autor"]}',
                    'fonte': f'{info["fonte"]}',
                },
            }
            if pagina: fragmento['pagina']=pagina
            return [fragmento]
            
        linhas = texto.replace('. ', '.\n')
        linhas = linhas.split('\n')
        while '' in linhas: linhas.remove('')
        
        fragmentos = []
        texto_fragmento = ''
        for idx in range(len(linhas)):
            if len(texto_fragmento.split(' ')) + len(linhas[idx].split(' ')) < comprimento_max_fragmento:
                texto_fragmento += ' ' + linhas[idx]
            else:
                fragmento = {
                    'page_content': texto_fragmento,
                    'metadata': {
                        'titulo': f'{info["titulo"]}',
                        'subtitulo':
                            f'Página {pagina} - Fragmento {len(fragmentos)+1}' if pagina
                            else f'Fragmento {len(fragmentos)+1}',
                        'autor': f'{info["autor"]}',
                        'fonte': f'{info["fonte"]}',
                    },
                }
                if pagina: fragmento['pagina'] = pagina
                fragmentos.append(fragmento)
                texto_fragmento = ''
            
        return fragmentos       
    
    def extrair_fragmento_txt(self, rotulo, info, comprimento_max_fragmento):
        with open(os.path.join(URL_LOCAL,info['url']), 'r', encoding='utf-8') as arq:
            texto = arq.read()
        
        fragmentos = self.processar_texto(texto, info, comprimento_max_fragmento)
        
        for idx in range(len(fragmentos)):
            fragmentos[idx]['id'] = f'{rotulo}:{idx+1}'
            fragmentos[idx]['metadata']['id'] = f'{rotulo}:{idx+1}'
        return fragmentos
    
    def extrair_fragmento_pdf(self, rotulo, info, comprimento_max_fragmento):
        fragmentos = []
        arquivo = PdfReader(os.path.join(URL_LOCAL,info['url']))
        for idx in range(len(arquivo.pages)):
            pagina = arquivo.pages[idx]
            texto = pagina.extract_text()
            fragmentos += self.processar_texto(texto, info, comprimento_max_fragmento, pagina=idx+1)
        for idx in range(len(fragmentos)): fragmentos[idx]['id'] = f'{rotulo}:{idx+1}'
        return fragmentos
        
    def extrair_fragmento_html(self, rotulo, info, comprimento_max_fragmento):
        with open(os.path.join(URL_LOCAL,info['url']), 'r', encoding='utf-8') as arq:
            conteudo_html = arq.read()
            
        pagina_html = BeautifulSoup(conteudo_html, 'html.parser')
        tags = pagina_html.find_all()
        texto = '\n'.join([tag.get_text() for tag in tags])
        
        fragmentos = self.processar_texto(texto, info, comprimento_max_fragmento)
        for idx in range(len(fragmentos)): fragmentos[idx]['id'] = f'{rotulo}:{idx+1}'
        return fragmentos
    
    extrair_fragmento_por_tipo = {
        'txt':  extrair_fragmento_txt,
        'pdf':  extrair_fragmento_pdf,
        'html': extrair_fragmento_html,
    }    
    
    def extrair_fragmentos(self,
        indice_documentos=None,
        comprimento_max_fragmento=COMPRIMENTO_MAX_FRAGMENTO):

        if not indice_documentos: indice_documentos = configuracoes.DOCUMENTOS

        fragmentos = []
        for rotulo, info in indice_documentos.items():
            print(f'Processando {rotulo}')
            url = info['url']
            tipo = url.split('.')[-1]
            fragmentos += self.extrair_fragmento_por_tipo[tipo](self, rotulo=rotulo, info=info, comprimento_max_fragmento=comprimento_max_fragmento)
        
        return fragmentos
        
    
    def gerar_banco(self,
            documentos,
            nome_banco_vetores=NOME_BANCO_VETORES,
            nome_colecao=NOME_COLECAO,
            instrucao=None,
            funcao_de_embeddings=None):
        
        # Utilizando o ChromaDb diretamente
        client = chromadb.PersistentClient(path=nome_banco_vetores)
        
        if not funcao_de_embeddings:
            funcao_de_embeddings = FuncaoEmbeddings(
                nome_modelo=EMBEDDING_INSTRUCTOR,
                tipo_modelo=SentenceTransformer,
                device=DEVICE,
                instrucao=instrucao)
        
        collection = client.create_collection(name=nome_colecao, embedding_function=funcao_de_embeddings, metadata={'hnsw:space': 'cosine'})
        
        print(f'Gerando >>> Banco {nome_banco_vetores} - Coleção {nome_colecao} - Instrução: {instrucao}')
        qtd_docs = len(documentos)
        for idx in range(qtd_docs):
            print(f'\r>>> Incluindo documento {idx+1} de {qtd_docs}', end='')
            doc = documentos[idx]
            collection.add(
                documents=[doc['page_content']],
                ids=[str(doc['id'])],
                metadatas=[doc['metadata']],
            )


        

        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key= os.environ.get("OPENAI_API_KEY", None),
                model_name="text-embedding-ada-002"
            )
        
        nome_colecao_openai = nome_colecao+'_openai'
        
        collection2 = client.create_collection(name=nome_colecao_openai, embedding_function=openai_ef, metadata={'hnsw:space': 'cosine'})
        
        print(f'Gerando >>> Banco {nome_banco_vetores} - Coleção {nome_colecao_openai} - Instrução: {instrucao}')
        qtd_docs = len(documentos)
        for idx in range(qtd_docs):
            print(f'\r>>> Incluindo documento {idx+1} de {qtd_docs}', end='')
            doc = documentos[idx]
            collection2.add(
                documents=[doc['page_content']],
                ids=[str(doc['id'])],
                metadatas=[doc['metadata']],
            )

        client._system.stop()
        
    def run(self,
            indice_documentos=None,
            nome_banco_vetores=NOME_BANCO_VETORES,
            nome_colecao=NOME_COLECAO,
            comprimento_max_fragmento=COMPRIMENTO_MAX_FRAGMENTO,
            instrucao=None,
            dados_funcao_de_embeddings=None):
        
        docs = self.extrair_fragmentos(
            indice_documentos=indice_documentos,
            comprimento_max_fragmento=comprimento_max_fragmento
        )
        
        self.gerar_banco(
            documentos=docs,
            nome_banco_vetores=nome_banco_vetores,
            nome_colecao=nome_colecao,
            instrucao=instrucao,
            funcao_de_embeddings=dados_funcao_de_embeddings['funcao_de_embeddings'] if dados_funcao_de_embeddings else None
        )

        with open(nome_banco_vetores+ '/descritor.json', 'w', encoding='utf-8') as arq:
            json.dump({
                "nome": nome_banco_vetores,
                "colecoes": [
                    {
                        "nome": nome_colecao,
                        "instrucao": instrucao,
                        "quantidade_max_palavras_por_documento": comprimento_max_fragmento,
                        # Se não for fornecida uma função, vai ser utilizada a padrão
                        "funcao_embeddings": dados_funcao_de_embeddings if dados_funcao_de_embeddings else {
                            "nome_modelo": "hkunlp/instructor-xl",
                            "tipo_modelo": "SentenceTransformer"
                        }
                    },
                ]
            }, arq, ensure_ascii=False, indent=4)
        
        
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Gera resultados de busca por documentos a partir de uma lista de perguntas")
    parser.add_argument('--url_indice_documentos', type=str, help="caminho para arquivo com a lista de documentos")
    parser.add_argument('--nome_banco_vetores', type=str, required=True, help="nome do banco de vetores a ser consultado")
    parser.add_argument('--nome_colecao', type=str, required=True, help="coleção do banco a ser utilizada")
    parser.add_argument('--comprimento_max_fragmento', type=int, required=True, help="número máximo de palavras por fragmento")
    parser.add_argument('--instrucao', type=str, help="instrucao a ser utilizada na função de embeddings")

    args = parser.parse_args()
    url_indice_documentos = None if not args.url_indice_documentos else args.url_indice_documentos

    if url_indice_documentos:
        with open(url_indice_documentos, 'r', encoding='utf-8') as arq:
            indice_documentos = json.load(arq)
    else:
        indice_documentos = None
            
    nome_banco_vetores = os.path.join(URL_LOCAL,"bancos_vetores/" + args.nome_banco_vetores)
    nome_colecao = args.nome_colecao
    comprimento_max_fragmento = args.comprimento_max_fragmento
    instrucao = None if not args.instrucao else args.instrucao

    gerador_banco_vetores = GeradorBancoVetores()
    gerador_banco_vetores.run(
        indice_documentos=indice_documentos,
        nome_banco_vetores=nome_banco_vetores,
        nome_colecao=nome_colecao,
        comprimento_max_fragmento=comprimento_max_fragmento,
        instrucao=instrucao)
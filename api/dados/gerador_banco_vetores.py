import argparse
import ast
import json
import os
import uuid
from api.configuracoes.config_gerais import configuracoes
from api.utils.interface_banco_vetores import FuncaoEmbeddings, FuncaoEmbeddingsOllama
from torch import cuda
import chromadb.utils.embedding_functions as embedding_functions
from sentence_transformers import SentenceTransformer
from chromadb import chromadb
from pypdf import PdfReader
from bs4 import BeautifulSoup

DEVICE='cuda' if cuda.is_available() else 'cpu'

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
                    'fonte': f'{info["fonte"]}#Art_{tit}'
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
        with open(os.path.join(configuracoes.url_pasta_documentos,info['url']), 'r', encoding='utf-8') as arq:
            texto = arq.read()
        
        fragmentos = self.processar_texto(texto, info, comprimento_max_fragmento)
        
        for idx in range(len(fragmentos)):
            fragmentos[idx]['metadata']['tag_fragmento'] = f'{rotulo}:{idx+1}'
        return fragmentos
    
    def extrair_fragmento_pdf(self, rotulo, info, comprimento_max_fragmento):
        fragmentos = []
        arquivo = PdfReader(os.path.join(configuracoes.url_pasta_documentos,info['url']))
        for idx in range(len(arquivo.pages)):
            pagina = arquivo.pages[idx]
            texto = pagina.extract_text()
            fragmentos += self.processar_texto(texto, info, comprimento_max_fragmento, pagina=idx+1)
        for idx in range(len(fragmentos)): fragmentos[idx]['id'] = f'{rotulo}:{idx+1}'
        return fragmentos
        
    def extrair_fragmento_html(self, rotulo, info, comprimento_max_fragmento):
        with open(os.path.join(configuracoes.url_pasta_documentos,info['url']), 'r', encoding='utf-8') as arq:
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
        comprimento_max_fragmento=configuracoes.num_maximo_palavras_por_fragmento):

        if not indice_documentos: indice_documentos = configuracoes.documentos

        fragmentos = []
        for rotulo, info in indice_documentos.items():
            print(f'Processando {rotulo}')
            url = info['url']
            tipo = url.split('.')[-1]
            fragmentos += self.extrair_fragmento_por_tipo[tipo](self, rotulo=rotulo, info=info, comprimento_max_fragmento=comprimento_max_fragmento)
        
        return fragmentos

    def obter_funcao_embeddings(self, nome_modelo: str=configuracoes.embedding_instructor, instrucao: str=None):
        if nome_modelo == configuracoes.embedding_instructor:
            funcao = FuncaoEmbeddings(
                nome_modelo=configuracoes.embedding_instructor,
                tipo_modelo=SentenceTransformer,
                device=DEVICE,
                instrucao=instrucao)
        elif nome_modelo == configuracoes.embedding_alibaba_gte:
            funcao = FuncaoEmbeddings(
                nome_modelo=configuracoes.embedding_alibaba_gte,
                tipo_modelo=SentenceTransformer,
                device=DEVICE)
        elif nome_modelo == configuracoes.embedding_bge_m3:
            funcao = FuncaoEmbeddings(
                nome_modelo=configuracoes.embedding_bge_m3,
                tipo_modelo=SentenceTransformer,
                device=DEVICE)
        elif nome_modelo == configuracoes.embedding_openai:
            funcao = embedding_functions.OpenAIEmbeddingFunction(
                api_key = os.environ.get("OPENAI_API_KEY", None),
                model_name=configuracoes.embedding_openai)
        elif nome_modelo == configuracoes.embedding_llama:
            funcao = FuncaoEmbeddingsOllama(
                nome_modelo=configuracoes.embedding_llama,
                url_api=configuracoes.url_llm)
        elif nome_modelo == configuracoes.embedding_deepseek:
            funcao = FuncaoEmbeddingsOllama(
                nome_modelo=configuracoes.embedding_deepseek,
                url_api=configuracoes.url_llm)
        elif nome_modelo == configuracoes.embedding_squad_portuguese:
            funcao = FuncaoEmbeddings(
                nome_modelo=configuracoes.embedding_squad_portuguese,
                tipo_modelo=SentenceTransformer,
                device=DEVICE
            )
        else:
            raise NameError(f'O tipo {nome_modelo} ainda não tem suporte para geração de função de embeddings implementado')
        
        return funcao
        
    
    def gerar_banco(self,
            documentos,
            url_banco_vetores=configuracoes.url_banco_vetores,
            nomes_colecoes=[configuracoes.nome_colecao_de_documentos],
            nomes_modelos_embeddings=[configuracoes.embedding_instructor],
            uuids_colecoes=[str(uuid.uuid4())],
            lista_instrucoes=None):
        
        # Utilizando o ChromaDb diretamente
        cliente_chroma = chromadb.PersistentClient(path=url_banco_vetores)
        
        if lista_instrucoes == None: lista_instrucoes = [None for item in nomes_modelos_embeddings]
        
        funcoes_embeddings = [
            self.obter_funcao_embeddings(
                nome_modelo=nomes_modelos_embeddings[idx],
                instrucao=lista_instrucoes[idx]
            ) for idx in range(len(nomes_modelos_embeddings))]
        
        hnsw_space = configuracoes.hnsw_space
        for idx in range(len(nomes_colecoes)):
            colecao = cliente_chroma.create_collection(name=nomes_colecoes[idx], embedding_function=funcoes_embeddings[idx], metadata={'hnsw:space': hnsw_space, 'uuid': uuids_colecoes[idx]})
        
            print(f'Gerando >>> Banco {url_banco_vetores} - Coleção {nomes_colecoes[idx]} - Embeddings {nomes_modelos_embeddings[idx]} - Instrução: {instrucao}')
            qtd_docs = len(documentos)
            for idx in range(qtd_docs):
                print(f'\r>>> Incluindo documento {idx+1} de {qtd_docs}', end='')
                doc = documentos[idx]
                
                uuid_doc = str(uuid.uuid4())
                doc['id'] = uuid_doc
                doc['metadata']['id'] = uuid_doc

                colecao.add(
                    documents=[doc['page_content']],
                    ids=[str(doc['id'])],
                    metadatas=[doc['metadata']],
                )
            print('-- Coleção concluída')

        cliente_chroma._system.stop()
        
    def executar(self,
            indice_documentos=None,
            url_banco_vetores=configuracoes.url_banco_vetores,
            nomes_colecoes=[configuracoes.nome_colecao_de_documentos],
            nomes_modelos_embeddings=[configuracoes.embedding_instructor],
            comprimento_max_fragmento=configuracoes.num_maximo_palavras_por_fragmento,
            lista_instrucoes=None):
        
        print(f"-- Geração de bancos vetoriais inicializada utilizando {DEVICE}...")
        
        docs = self.extrair_fragmentos(
            indice_documentos=indice_documentos,
            comprimento_max_fragmento=comprimento_max_fragmento
        )
        
        uuids_colecoes = [str(uuid.uuid4()) for colecao in nomes_colecoes]
        self.gerar_banco(
            documentos=docs,
            url_banco_vetores=url_banco_vetores,
            nomes_colecoes=nomes_colecoes,
            nomes_modelos_embeddings=nomes_modelos_embeddings,
            uuids_colecoes=uuids_colecoes,
            lista_instrucoes=lista_instrucoes
        )

        tipos_modelos = {
            configuracoes.embedding_instructor: 'SentenceTransformer/Instructor',
            configuracoes.embedding_openai: 'OpenAI-API',
            configuracoes.embedding_alibaba_gte: 'SentenceTransformer/Alibaba-GTE',
            configuracoes.embedding_squad_portuguese: 'SentenceTransformer/Bert-Squad-Pt',
            configuracoes.embedding_llama: 'Llama',
            configuracoes.embedding_deepseek: 'Deepseek-r1',
            configuracoes.embedding_bge_m3: 'BGE-M3'
        }
        descritor = {
            "nome": url_banco_vetores.split('/')[-1],
            "colecoes": [
                {
                    "uuid": uuids_colecoes[idx],
                    "nome": nomes_colecoes[idx],
                    "instrucao": lista_instrucoes[idx],
                    "quantidade_max_palavras_por_documento": comprimento_max_fragmento,
                    "hnsw:space": configuracoes.hnsw_space,
                    # Se não for fornecida uma função, vai ser utilizada a padrão
                    "funcao_embeddings": {
                        "nome_modelo": nomes_modelos_embeddings[idx],
                        "tipo_modelo": tipos_modelos[nomes_modelos_embeddings[idx]]
                    }
                } for idx in range(len(nomes_colecoes))
            ]
        }
        
        try:
            with open(url_banco_vetores+ '/descritor.json', 'r', encoding='utf-8') as arq:
                descritor_existente = json.load(arq)
            descritor_existente['colecoes'] += descritor['colecoes']

            with open(url_banco_vetores+ '/descritor.json', 'w', encoding='utf-8') as arq:
                json.dump(descritor_existente, arq, ensure_ascii=False, indent=4)
                
        except FileNotFoundError:
            with open(url_banco_vetores+ '/descritor.json', 'w', encoding='utf-8') as arq:
                json.dump(descritor, arq, ensure_ascii=False, indent=4)
        
        if configuracoes.usar_wandb:    
            import wandb
            run=wandb.init(project=configuracoes.wandb_nome_projeto, job_type='ingest', config=descritor)
            idx_artif = wandb.Artifact(name='banco-vetorial-chroma', type='banco-vetorial')
            idx_artif.add_dir(url_banco_vetores)
            run.log_artifact(idx_artif)
            #run.use_artifact(configuracoes.wandb_uri_artefato_banco_vetorial, type='banco-vetorial').download(root='./api/dados/bancos_vetores/')
        
        
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Gera um banco vetorial a partir de uma lista de documentos")
    parser.add_argument('--url_indice_documentos', type=str, help="caminho para arquivo com a lista de documentos")
    parser.add_argument('--nome_banco_vetores', type=str, required=True, help="nome do banco de vetores a ser criado")
    parser.add_argument('--lista_colecoes', type=str, required=True, help='''uma lista com os nomes das coleções no formato "['colecao1', 'colecao2']''')
    parser.add_argument('--lista_nomes_modelos_embeddings', type=str, required=True, help='''uma lista com os tipos das funções de embeddings no formato "['openai', 'instructor']''')
    parser.add_argument('--comprimento_max_fragmento', type=int, required=True, help="número máximo de palavras por fragmento")
    parser.add_argument('--lista_instrucoes', type=str, help="lsita de instrucoes a serem utilizadas nas funções de embeddings de modelos")

    args = parser.parse_args()
    url_indice_documentos = None if not args.url_indice_documentos else args.url_indice_documentos

    if url_indice_documentos:
        with open(url_indice_documentos, 'r', encoding='utf-8') as arq:
            indice_documentos = json.load(arq)
    else:
        indice_documentos = None
            
    nome_banco_vetores = os.path.join(configuracoes.url_pasta_bancos_vetores, args.nome_banco_vetores)
    
    nomes_colecoes = ast.literal_eval(args.lista_colecoes)
    nomes_modelos_embeddings = ast.literal_eval(args.lista_nomes_modelos_embeddings)
    if not isinstance(nomes_colecoes, list) or not isinstance(nomes_modelos_embeddings, list) or len(nomes_colecoes) != len(nomes_modelos_embeddings):
        raise ValueError('Problema ao processar argumentos de coleções e funções de embeddings')
    
    comprimento_max_fragmento = args.comprimento_max_fragmento
    lista_instrucoes = None if not args.lista_instrucoes else args.lista_instrucoes

    gerador_banco_vetores = GeradorBancoVetores()
    gerador_banco_vetores.executar(
        indice_documentos=indice_documentos,
        url_banco_vetores=nome_banco_vetores,
        nomes_colecoes=nomes_colecoes,
        nomes_modelos_embeddings=nomes_modelos_embeddings,
        comprimento_max_fragmento=comprimento_max_fragmento,
        lista_instrucoes=lista_instrucoes)
    
## Modelo de Execução
# python -m api.dados.gerador_banco_vetores \
# --nome_banco_vetores banco_assistente \
# --lista_colecoes "['documentos_rh_instructor', 'documentos_rh_openai', 'documentos_rh_alibaba', 'documentos_rh_llama', 'documentos_rh_deepseek-r1', 'documentos_rh_bert_pt']" \
# --lista_nomes_modelos_embeddings "['hkunlp/instructor-xl', 'text-embedding-ada-002', 'Alibaba-NLP/gte-multilingual-base', 'llama3.1', 'deepseek-r1:14b', 'pierreguillou/bert-base-cased-squad-v1.1-portuguese']" \
# --comprimento_max_fragmento 300
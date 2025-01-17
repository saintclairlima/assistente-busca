from typing import Tuple
import uuid
from chromadb import chromadb
import json
import sqlite3
from api.configuracoes.config_gerais import configuracoes


class InterfacePersistencia:
    def __init__(self, url_banco):
        self.url_banco = url_banco

class InterfacePersistenciaSQLite(InterfacePersistencia):
    def __init__(self, url_banco):
        super().__init__(url_banco)
    
    def executar_script(self, script: str):
        with sqlite3.connect(self.url_banco) as conexao:
            try:
                cursor  = conexao.cursor()
                cursor.executescript(script)
                print(f'Tabelas criadas em {self.url_banco}')
                conexao.commit()
            except sqlite3.Error as e:
                print(f"Ocorreu um erro: {e}")
                raise
        
    def __insert(self, query: str, dados: tuple):
        with sqlite3.connect(self.url_banco) as conexao:
            cursor  = conexao.cursor()
            cursor.execute(query, dados)
            conexao.commit()
            return cursor.lastrowid
        
    def executar_query_insercao(self, query: str, dados: tuple):
        return self.__insert(query, dados)
    
    def __insert_multiplo(self, multiplas_queries: list, multiplos_dados: list):
        ids_insercoes = {}
        with sqlite3.connect(self.url_banco) as conexao:
            try:
                cursor = conexao.cursor()
                parametros = list(zip(multiplas_queries, multiplos_dados))
                for idx in range(len(parametros)):
                    query, dados = parametros[idx]
                    cursor.execute(query, dados)
                    ids_insercoes[idx] = cursor.lastrowid
                conexao.commit()
                return ids_insercoes
            except sqlite3.Error as e:
                # Rollback the transaction if any error occurs
                conexao.rollback()
                raise
        
    def executar_query_insercao_multipla(self, multiplas_queries: list, multiplos_dados: list):
        return self.__insert_multiplo(multiplas_queries, multiplos_dados)
            
    def __update(self, query: str, dados: tuple):
        with sqlite3.connect(self.url_banco) as conexao:
            cursor  = conexao.cursor()
            cursor.execute(query, dados)
            conexao.commit()
            return cursor.rowcount
            
    def __select(self, tabela: str, colunas: tuple):
        query = f'''SELECT {','.join(colunas)} FROM {tabela}'''
        with sqlite3.connect(self.url_banco) as conexao:
            cursor  = conexao.cursor()
            cursor.execute(query)
            conexao.commit()
            return cursor.fetchall()
    
    def executar_query_select(self, tabela: str, colunas: Tuple[str], query_select: str=None):
        if query_select:
            with sqlite3.connect(self.url_banco) as conexao:
                cursor  = conexao.cursor()
                cursor.execute(query_select)
                conexao.commit()
                return cursor.fetchall()
        return self.__select(tabela, colunas)
        
class GerenciadorPersistenciaSQLite:

    def __init__(self, url_arquivo_sqlite: str=configuracoes.url_banco_sql):
        self.url_arquivo_sqlite = url_arquivo_sqlite

    def inicializar_banco_SQLite(self, url_script_sql: str=configuracoes.url_script_geracao_banco_sqlite):
        banco_sqlite = InterfacePersistenciaSQLite(self.url_arquivo_sqlite)
        print(f"Inicializando banco {self.url_arquivo_sqlite} usando {url_script_sql}")
        with open(url_script_sql, 'r') as arq:
            script = arq.read()
        
        banco_sqlite.executar_script(script=script)

    def persistir_dados_colecao(self, url_descritor_banco_vetorial: str, url_arquivo_sqlite: str=configuracoes.url_banco_sql):
        with open(url_descritor_banco_vetorial, 'r', encoding='utf-8') as arq:
            desc_banco_vetorial = json.load(arq)
            
        banco_sqlite = InterfacePersistenciaSQLite(url_arquivo_sqlite)
        ids_colecoes_salvas={}
        for colecao in desc_banco_vetorial['colecoes']:
            uuid_colecao=colecao['uuid']
            nome=colecao['nome']
            nome_banco_vetores=desc_banco_vetorial['nome']
            modelo_fn_embd=colecao['funcao_embeddings']['nome_modelo']
            tipo_modelo_fn_embd=colecao['funcao_embeddings']['tipo_modelo']
            instrucao=colecao['instrucao']
            qtd_max_palavras=colecao['quantidade_max_palavras_por_documento']
            metrica_similaridade=colecao['hnsw:space']
            
            query='INSERT INTO Colecao '+ \
                '(UUID_Colecao, Nome, Banco_Vetores, Nome_Modelo_Fn_Embeddings, Tipo_Modelo_Fn_Embeddings, Instrucao, Qtd_Max_Palavras, Metrica_Similaridade) ' +\
                'VALUES(?,?,?,?,?,?,?,?,?);'
            valores=(uuid_colecao, nome, nome_banco_vetores, modelo_fn_embd, tipo_modelo_fn_embd, instrucao, qtd_max_palavras, metrica_similaridade)
            id_colecao_salva = banco_sqlite.executar_query_insercao(query, valores)
            print(f'Coleção {nome} salva em {url_arquivo_sqlite} com id {id_colecao_salva}')
            ids_colecoes_salvas[colecao['nome']]=id_colecao_salva
        
        return ids_colecoes_salvas
    
    def persistir_documentos(self, url_descritor_banco_vetorial: str, url_arquivo_sqlite: str=configuracoes.url_banco_sql):
        with open(url_descritor_banco_vetorial, 'r', encoding='utf-8') as arq:
            desc_banco_vetorial = json.load(arq)
            
        banco_sqlite = InterfacePersistenciaSQLite(url_arquivo_sqlite)
        colecoes_uuids = {
            resultado[1]: resultado[0]
            for resultado in banco_sqlite.executar_query_select('colecao', ['uuid', 'nome'])
        }
        
        query_inserir_doc = 'INSERT INTO Documento ' + \
                            '(UUID_Documento, Tag_Fragmento, Conteudo, Titulo, Subtitulo, Autor, Fonte, UUID_Colecao) ' + \
                            'VALUES (?,?,?,?,?,?,?,?);'
                
        client = chromadb.PersistentClient(path=f'''api/dados/bancos_vetores/{desc_banco_vetorial['nome']}''')
        
        docs_inseridos={}
        for colecao in desc_banco_vetorial['colecoes']:
            collection = client.get_collection(name=colecao['nome'])
            documentos = collection.get()
            
            documentos = [
                {
                    'id': documentos['ids'][idx],
                    'conteudo': documentos['documents'][idx],
                    'metadados':  documentos['metadatas'][idx],
                }
                for idx in range(len(documentos['ids']))
            ]
            for doc in documentos:
                uuid_documento=doc['metadados']['id']
                tag_fragmento=doc['metadados']['tag_fragmento']
                conteudo=doc['conteudo']
                titulo=doc['metadados']['titulo']
                subtitulo=doc['metadados']['subtitulo']
                autor=doc['metadados']['autor']
                fonte=doc['metadados']['fonte']
                uuid_colecao=colecoes_uuids[colecao['nome']]
                
                dados = [uuid_documento, tag_fragmento, conteudo, titulo, subtitulo, autor, fonte, uuid_colecao]
                
                id_doc_inserido = banco_sqlite.executar_query_insercao(query=query_inserir_doc, dados=dados)
                docs_inseridos[uuid_documento] = id_doc_inserido
                
        client._system.stop()
        
        return docs_inseridos
    
    def persistir_interacao(self, dados_interacao: dict, url_arquivo_sqlite: str=configuracoes.url_banco_sql):

        multiplas_queries = []
        multiplos_dados = []

        banco_sqlite = InterfacePersistenciaSQLite(url_arquivo_sqlite)
        query_inserir_interacao = 'INSERT INTO Interacao ' + \
                                  '(UUID_Interacao, Pergunta, Tipo_Dispositivo_Aplicacao, Tipo_Dispositivo_LLM, Tempo_Recuperacao_Documentos, ' + \
                                  'Tempo_Estimativa_Bert, LLM_Template_System, LLM_Historico, LLM_Cliente, LLM_Nome_Modelo, ' + \
                                  'LLM_Tempo_Carregamento, LLM_Num_Tokens_Prompt, LLM_Tempo_Processamento_Prompt, LLM_Num_Tokens_Resposta, ' + \
                                  'LLM_Tempo_Processamento_Resposta, LLM_Tempo_Inicio_Stream, LLM_Tempo_Total, LLM_Resposta, LLM_Tipo_Conclusao, JSON_Interacao) ' + \
                                  'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'

        dados_interacao['uuid_interacao'] = str(uuid.uuid4())
        dados_inserir_interacao=(
            dados_interacao['uuid_interacao'],
            dados_interacao['pergunta'],
            dados_interacao['tipo_dispositivo_aplicacao'],
            dados_interacao['tipo_dispositivo_llm'],
            dados_interacao['tempo_recuperacao_documentos'],
            dados_interacao['tempo_estimativa_bert'],
            dados_interacao['template_system_llm'],
            str(dados_interacao['historico_llm']),
            dados_interacao['cliente_llm'],
            dados_interacao['modelo_llm'],
            dados_interacao['resposta_completa_llm']['load_duration'] / 1_000_000_000,         # tempo_carregamento_llm
            dados_interacao['resposta_completa_llm']['prompt_eval_count'],                     # num_tokens_promt
            dados_interacao['resposta_completa_llm']['prompt_eval_duration']  / 1_000_000_000, # tempo_processamento_prompt
            dados_interacao['resposta_completa_llm']['eval_count'],                            # num_tokens_resposta
            dados_interacao['resposta_completa_llm']['eval_duration']  / 1_000_000_000,        # tempo_geracao_resposta
            dados_interacao['tempo_inicio_stream_resposta'],
            dados_interacao['tempo_total_llm'],
            dados_interacao['resposta'],
            dados_interacao['resposta_completa_llm']['done_reason'],                           # tipo_conclusao_llm
            json.dumps(dados_interacao)                                                        # conteúdo completo da interação em json-string
        )

        multiplas_queries.append(query_inserir_interacao)
        multiplos_dados.append(dados_inserir_interacao)
        
        query_inserir_doc_interacao = 'INSERT INTO Documento_em_Interacao ' + \
                                      '(UUID_Documento, UUID_Interacao, Resposta_Bert, Score_Bert, Score_Distancia, Score_Ponderado)' + \
                                      'VALUES(?,?,?,?,?,?);'

        for doc in dados_interacao['documentos']:
            dados_inserir_doc_interacao = (
                # AFAZER: Ajustar quando remover a dupla estimativa do BERT
                doc['id'],
                dados_interacao['uuid_interacao'],
                doc['resposta_bert'][0],
                doc['score_bert'][2],
                doc['score_distancia'],
                doc['score_ponderado']
            )

            multiplas_queries.append(query_inserir_doc_interacao)
            multiplos_dados.append(dados_inserir_doc_interacao)
        
        return banco_sqlite.executar_query_insercao_multipla(multiplas_queries=multiplas_queries, multiplos_dados=multiplos_dados)
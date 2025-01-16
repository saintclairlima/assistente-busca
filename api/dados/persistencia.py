from typing import Tuple
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
        
    def __insert(self, query: str, dados: tuple):
        with sqlite3.connect(self.url_banco) as conexao:
            cursor  = conexao.cursor()
            cursor.execute(query, dados)
            conexao.commit()
            return cursor.lastrowid
    
    def inicializar_banco_sqlite(self, url_script_sql: str):
        pass
        
    def executar_query_insercao(self, query: str, dados: tuple):
        return self.__insert(query, dados)
            
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
    def persistir_dados_colecao(self, url_descritor_banco_vetorial: str, url_arquivo_sqlite: str):
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
    
    def persistir_documentos(self, url_descritor_banco_vetorial: str, url_arquivo_sqlite: str):
        with open(url_descritor_banco_vetorial, 'r', encoding='utf-8') as arq:
            desc_banco_vetorial = json.load(arq)
            
        banco_sqlite = InterfacePersistenciaSQLite(url_arquivo_sqlite)
        colecoes_uuids = {
            resultado[1]: resultado[0]
            for resultado in banco_sqlite.executar_query_select('colecao', ['uuid', 'nome'])
        }
        
        query_inserir_doc = 'INSERT INTO Documento ' + \
                            '(UUID_Documento, Tag_Fragmento, Conteudo, Titulo, Subtitulo, Autor, Fonte, UUID_Colecao) ' + \
                            'VALUES (?,?,?,?,?,?,?,?)'
                
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
                
from chromadb import chromadb
import json
import sqlite3


class InterfacePersistencia:
    def __init__(self, url_banco):
        self.url_banco = url_banco
    
    def executar_query(query, dados):
        raise NotImplementedError('Método executar_query() não implementado nesta classe.')

class InterfacePersistenciaSQLite(InterfacePersistencia):
    def __init__(self, url_banco):
        super().__init__(url_banco)
        
    def __insert(self, query: str, dados: tuple):
        with sqlite3.connect(self.url_banco) as conexao:
            cursor  = conexao.cursor()
            cursor.execute(query, dados)
            conexao.commit()
            return cursor.lastrowid
        
    def executar_query_insercao(self, query: str, dados: tuple):
        return self.__insert(query, dados)
            
    def __update(self, query: str, dados: tuple):
        with sqlite3.connect(self.url_banco) as conexao:
            cursor  = conexao.cursor()
            cursor.execute(query, dados)
            conexao.commit()
            return cursor.rowcount
            
    def __select(self, query: str, dados: tuple):
        with sqlite3.connect(self.url_banco) as conexao:
            cursor  = conexao.cursor()
            cursor.execute(query, dados)
            conexao.commit()
            return cursor.fetchall()
        
class GerenciadorPersistenciaSQLite:
    def persistir_dados_colecao(self, url_descritor_banco_vetorial: str, url_arquivo_sqlite: str):
        with open(url_descritor_banco_vetorial, 'r', encoding='utf-8') as arq:
            desc_banco_vetorial = json.load(arq)
            
        banco_sqlite = InterfacePersistenciaSQLite(url_arquivo_sqlite)
        ids_colecoes_salvas=[]
        for colecao in desc_banco_vetorial['colecoes']:
            id=None
            nome=colecao['nome']
            nome_banco_vetores=desc_banco_vetorial['nome']
            modelo_fn_embd=colecao["funcao_embeddings"]["nome_modelo"]
            tipo_modelo_fn_embd=colecao["funcao_embeddings"]["tipo_modelo"]
            instrucao=colecao["instrucao"]
            qtd_max_palavras=colecao['quantidade_max_palavras_por_documento']
            
            query='INSERT INTO Colecao VALUES(?,?,?,?,?,?,?);'
            valores=(id, nome, nome_banco_vetores, modelo_fn_embd, tipo_modelo_fn_embd, instrucao, qtd_max_palavras)
            id_colecao_salva = banco_sqlite.executar_query_insercao(query, valores)
            print(f'Coleção {nome} salva em {url_arquivo_sqlite} com id {id_colecao_salva}')
            ids_colecoes_salvas.append(id_colecao_salva)
        
        return ids_colecoes_salvas

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
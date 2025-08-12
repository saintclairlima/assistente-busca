import os
from typing import Tuple
import uuid
from chromadb import chromadb
import json
import sqlite3
import pymssql
from api.configuracoes.config_gerais import configuracoes


class InterfacePersistencia:
    def __init__(self):
        pass
    
    def executar_script(self, script: str):
        raise NotImplementedError('Método executar_script() não foi implantado para esta classe')
        
    def __insert(self, query: str, dados: tuple):
        raise NotImplementedError('Método __insert() não foi implantado para esta classe')
    
    def __insert_multiplo(self, multiplas_queries: list, multiplos_dados: list):
        raise NotImplementedError('Método __insert_multiplo() não foi implantado para esta classe')
            
    def __update(self, query: str, dados: tuple):
        raise NotImplementedError('Método __update() não foi implantado para esta classe')
            
    def __select(self, tabela: str, colunas: tuple):
        raise NotImplementedError('Método __select() não foi implantado para esta classe')


class InterfacePersistenciaSQL(InterfacePersistencia):
    def __init__(self, url_banco, encryption, porta, usuario, senha, database):
        
        super().__init__()
        self.parametros = {
            'host': url_banco,
            'encryption': encryption, 
            'port': porta,
            'user': usuario,
            'password': senha,
            'database': database
        }
    
    def executar_script(self, script: str):
        with pymssql.connect(**self.parametros) as conexao:
            try:
                cursor = conexao.cursor()
                for statement in script.split(';'):
                    # Executa statements não vazios
                    if statement.strip():
                        cursor.execute(statement)
                print(f'''Tabelas criadas em {self.parametros['host']}:{self.parametros['port']}/{self.parametros['database']}''')
                conexao.commit()
            except pymssql.Error as e:
                print(f"Ocorreu um erro na escrita das tabelas: {e}")
                raise
            except Exception as e:
                print(f"Ocorreu um erro inesperado: {e}")
                raise
            finally:
                cursor.close()
        
    def __insert(self, query: str, dados: tuple):
        with pymssql.connect(**self.parametros) as conexao:
            query = query.replace('?', '%s')
            try:
                cursor = conexao.cursor()
                cursor.execute(query, dados)
                num_linhas = cursor.rowcount
                conexao.commit()
                return num_linhas
            finally:
                cursor.close()
        
    def executar_query_insercao(self, query: str, dados: tuple):
        return self.__insert(query, dados)
    
    def __insert_multiplo(self, multiplas_queries: list, multiplos_dados: list):
        ids_insercoes = {}
        with pymssql.connect(**self.parametros) as conexao:
            try:
                cursor = conexao.cursor()
                parametros = list(zip(multiplas_queries, multiplos_dados))
                for idx in range(len(parametros)):
                    query, dados = parametros[idx]
                    query = query.replace('?', '%s')
                    cursor.execute(query, dados)
                    ids_insercoes[idx] = cursor.lastrowid
                conexao.commit()
                return ids_insercoes
            except pymssql.Error as e:
                # Rollback the transaction if any error occurs
                conexao.rollback()
                raise
            finally:
                cursor.close()
        
    def executar_query_insercao_multipla(self, multiplas_queries: list, multiplos_dados: list):
        return self.__insert_multiplo(multiplas_queries, multiplos_dados)
            
    def __update(self, query: str, dados: tuple):
        with pymssql.connect(**self.parametros) as conexao:
            try:
                query = query.replace('?', '%s')
                cursor = conexao.cursor()
                cursor.execute(query, dados)
                num_linhas = cursor.rowcount
                conexao.commit()
                return num_linhas
            finally:
                cursor.close()
    
    def executar_query_update(self, query: str, dados: tuple):
        return self.__update(query, dados)
            
    def __select(self, tabela: str, colunas: tuple):
        query = f'''SELECT {', '.join(colunas)} FROM {configuracoes.configuracoes_banco_sql()['schema']}.{tabela}'''
        with pymssql.connect(**self.parametros) as conexao:
            try:
                cursor = conexao.cursor()
                cursor.execute('SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED')
                cursor.execute(query)
                resultado = cursor.fetchall()
                conexao.commit()
                return resultado
            finally:
                cursor.close()
    
    def executar_query_select(self, tabela: str=None, colunas: Tuple[str]=None, query: str=None, dados: Tuple[str]=None):
        if query and dados:
            with pymssql.connect(**self.parametros) as conexao:
                try:
                    query = query.replace('?', '%s')
                    cursor  = conexao.cursor()
                    cursor.execute(query, dados)
                    dados = cursor.fetchall()
                    conexao.commit()
                    return dados
                finally:
                    cursor.close()
        elif tabela == None == colunas:
            raise ValueError("Valores não fornecidos para a tabela e as colunas")
            
        return self.__select(tabela, colunas)


class InterfacePersistenciaSQLite(InterfacePersistencia):
    def __init__(self, url_banco):
        super().__init__()
        self.url_banco=url_banco
    
    def executar_script(self, script: str):
        with sqlite3.connect(self.url_banco) as conexao:
            try:
                conexao.executescript(script)
                print(f'Dados persistidos em {self.url_banco}')
                conexao.commit()
            except sqlite3.Error as e:
                print(f"Ocorreu um erro: {e}")
                raise
        
    def __insert(self, query: str, dados: tuple):
        with sqlite3.connect(self.url_banco) as conexao:
            try:
                conexao.execute("PRAGMA foreign_keys = ON;")
                cursor = conexao.execute(query, dados)
                num_linhas = cursor.rowcount
                conexao.commit()
                return num_linhas
            finally:
                cursor.close()
        
    def executar_query_insercao(self, query: str, dados: tuple):
        return self.__insert(query, dados)
    
    def __insert_multiplo(self, multiplas_queries: list, multiplos_dados: list):
        ids_insercoes = {}
        with sqlite3.connect(self.url_banco) as conexao:
            conexao.execute("PRAGMA foreign_keys = ON;")
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
            finally:
                cursor.close()
        
    def executar_query_insercao_multipla(self, multiplas_queries: list, multiplos_dados: list):
        return self.__insert_multiplo(multiplas_queries, multiplos_dados)
            
    def __update(self, query: str, dados: tuple):
        with sqlite3.connect(self.url_banco) as conexao:
            try:
                conexao.execute("PRAGMA foreign_keys = ON;")
                cursor = conexao.execute(query, dados)
                num_linhas = cursor.rowcount
                conexao.commit()
                return num_linhas
            finally:
                cursor.close()
    
    def executar_query_update(self, query: str, dados: tuple):
        return self.__update(query, dados)
            
    def __select(self, tabela: str, colunas: tuple):
        query = f'''SELECT {','.join(colunas)} FROM {tabela}'''
        with sqlite3.connect(self.url_banco) as conexao:
            try:
                cursor = conexao.cursor()
                cursor.execute(query)
                resultado = cursor.fetchall()
                conexao.commit()
                return resultado
            finally:
                cursor.close()
    
    def executar_query_select(self, tabela: str=None, colunas: Tuple[str]=None, query: str=None, dados: Tuple[str]=None):
        if query and dados:
            with sqlite3.connect(self.url_banco) as conexao:
                try:
                    cursor  = conexao.cursor()
                    cursor.execute(query, dados)
                    resultado = cursor.fetchall()
                    conexao.commit()
                    return resultado
                finally:
                    cursor.close()
        elif tabela == None == colunas:
            raise ValueError("Valores não fornecidos para a tabela e as colunas")
            
        return self.__select(tabela, colunas)


class GerenciadorPersistencia:

    def __init__(self, info_banco: dict, classeInterface: type):
        self.info_banco = info_banco
        self.classeInterface = classeInterface

    def obter_conexao_banco(self):
        return self.classeInterface(**self.info_banco['parametros'])

    def inicializar_banco(self, url_script_sql: str=configuracoes.url_script_geracao_banco_sqlite):

        banco_dados = self.classeInterface(**self.info_banco['parametros'])

        print(f"Inicializando banco ({self.info_banco['tipo_persistencia']}) {self.info_banco['nome_banco']} usando {url_script_sql}")
        with open(url_script_sql, 'r') as arq:
            script = arq.read()
        
        banco_dados.executar_script(script=script)

    def persistir_dados_colecao(self, url_descritor_banco_vetorial: str,):
        with open(url_descritor_banco_vetorial, 'r', encoding='utf-8') as arq:
            desc_banco_vetorial = json.load(arq)
            
        banco_dados = self.classeInterface(**self.info_banco['parametros'])
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
                'VALUES(?,?,?,?,?,?,?,?);'
            valores=(uuid_colecao, nome, nome_banco_vetores, modelo_fn_embd, tipo_modelo_fn_embd, instrucao, qtd_max_palavras, metrica_similaridade)
            id_colecao_salva = banco_dados.executar_query_insercao(query, valores)
            print(f'''Coleção {nome} salva em {self.info_banco['nome_banco']} com id {id_colecao_salva}''')
            ids_colecoes_salvas[colecao['nome']]=id_colecao_salva
        
        return ids_colecoes_salvas
    
    def persistir_documentos(self, url_descritor_banco_vetorial: str):
        with open(url_descritor_banco_vetorial, 'r', encoding='utf-8') as arq:
            desc_banco_vetorial = json.load(arq)
            
        banco_dados = self.classeInterface(**self.info_banco['parametros'])
        colecoes_uuids = {
            resultado[1]: resultado[0]
            for resultado in banco_dados.executar_query_select(tabela='colecao', colunas=['uuid_colecao', 'nome'])
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
                
                id_doc_inserido = banco_dados.executar_query_insercao(query=query_inserir_doc, dados=dados)
                docs_inseridos[uuid_documento] = id_doc_inserido
                
        client._system.stop()
        
        return docs_inseridos
    
    def persistir_interacao(self, dados_interacao: dict):

        multiplas_queries = []
        multiplos_dados = []

        banco_dados = self.classeInterface(**self.info_banco['parametros'])
        query_inserir_interacao = 'INSERT INTO Interacao ' + \
                                  '(UUID_Interacao, Pergunta, Tipo_Dispositivo_Aplicacao, Tipo_Dispositivo_LLM, Tempo_Recuperacao_Documentos, ' + \
                                  'Tempo_Estimativa_Bert, LLM_Template_System, LLM_Historico, LLM_Cliente, LLM_Nome_Modelo, ' + \
                                  'LLM_Tempo_Carregamento, LLM_Num_Tokens_Prompt, LLM_Tempo_Processamento_Prompt, LLM_Num_Tokens_Resposta, ' + \
                                  'LLM_Tempo_Processamento_Resposta, LLM_Tempo_Inicio_Stream, LLM_Tempo_Total, LLM_Resposta, ' + \
                                  'LLM_Tipo_Conclusao, Intencao, JSON_Interacao, UUID_Sessao, UUID_Cliente) ' + \
                                  'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'

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
            dados_interacao['resposta_completa_llm']['load_duration'] / 1_000_000_000 if dados_interacao['resposta_completa_llm'] else None,         # tempo_carregamento_llm
            dados_interacao['resposta_completa_llm']['prompt_eval_count'] if dados_interacao['resposta_completa_llm'] else None,                     # num_tokens_promt
            dados_interacao['resposta_completa_llm']['prompt_eval_duration']  / 1_000_000_000 if dados_interacao['resposta_completa_llm'] else None, # tempo_processamento_prompt
            dados_interacao['resposta_completa_llm']['eval_count'] if dados_interacao['resposta_completa_llm'] else None,                            # num_tokens_resposta
            dados_interacao['resposta_completa_llm']['eval_duration']  / 1_000_000_000 if dados_interacao['resposta_completa_llm'] else None,        # tempo_geracao_resposta
            dados_interacao['tempo_inicio_stream_resposta'],
            dados_interacao['tempo_total_llm'],
            dados_interacao['resposta'],
            dados_interacao['resposta_completa_llm']['done_reason'] if dados_interacao['resposta_completa_llm'] else None,                           # tipo_conclusao_llm
            dados_interacao['intencao'],                                                                                                             # intenção do usuário segundo predito pelo classificador
            json.dumps(dados_interacao, ensure_ascii=False),                                                                                         # conteúdo completo da interação em json-string
            dados_interacao['id_sessao'],                                                                                                            # identificador da sessão de que a intereção faz parte
            dados_interacao['id_cliente']
        )

        multiplas_queries.append(query_inserir_interacao)
        multiplos_dados.append(dados_inserir_interacao)
        
        query_inserir_doc_interacao = 'INSERT INTO Documento_em_Interacao ' + \
                                      '(UUID_Documento, UUID_Interacao, Resposta_Bert, Score_Bert, Score_Distancia, Score_Ponderado)' + \
                                      'VALUES(?,?,?,?,?,?);'

        for doc in dados_interacao['documentos']:
            dados_inserir_doc_interacao = (
                doc['id'],
                dados_interacao['uuid_interacao'],
                doc['resposta_bert'],
                doc['score_bert'][0],
                doc['score_distancia'],
                doc['score_ponderado']
            )

            multiplas_queries.append(query_inserir_doc_interacao)
            multiplos_dados.append(dados_inserir_doc_interacao)
        try:
            banco_dados.executar_query_insercao_multipla(multiplas_queries=multiplas_queries, multiplos_dados=multiplos_dados)
            return dados_interacao['uuid_interacao']
        except Exception as e:
            print(f'Ocorreu um erro: {e}')
            raise

    def persistir_avaliacao(self, dados_avaliacao: dict):
        banco_dados = self.classeInterface(**self.info_banco['parametros'])

        # AFAZER: implementar select com where nas interfaces de persistência
        query = f'''SELECT * FROM Avaliacao_Interacao WHERE UUID_Interacao = ?;'''
        dados = (dados_avaliacao['uuid_interacao'],)

        resultados = banco_dados.executar_query_select(query=query, dados=dados)

        if len(resultados) == 0:
            query_inserir_avaliacao = 'INSERT INTO Avaliacao_Interacao ' + \
                                      '(UUID_Interacao, Avaliacao, Comentario) ' + \
                                      'VALUES (?,?,?);'
            
            dados_inserir_avaliacao = (dados_avaliacao['uuid_interacao'], dados_avaliacao['avaliacao'], dados_avaliacao['comentario'])

            try:
                return banco_dados.executar_query_insercao(query=query_inserir_avaliacao, dados=dados_inserir_avaliacao)
            except Exception as e:
                print(f'Ocorreu um erro: {e}')
                raise
        else:
            query_atualizar_avaliacao = 'UPDATE Avaliacao_Interacao ' + \
                                        'SET Avaliacao=?, Comentario=? ' + \
                                        'WHERE UUID_Interacao = ?;'
            
            dados_atualizar_avaliacao =  (dados_avaliacao['avaliacao'], dados_avaliacao['comentario'], dados_avaliacao['uuid_interacao'])
            try:
                return banco_dados.executar_query_update(query=query_atualizar_avaliacao, dados=dados_atualizar_avaliacao)
            except Exception as e:
                print(f'Ocorreu um erro: {e}')
                raise


class GerenciadorPersistenciaSQLite(GerenciadorPersistencia):
    def __init__(self, info_banco: dict=configuracoes.configuracoes_banco_sqlite()):
        super().__init__(
            info_banco=info_banco,
            classeInterface=InterfacePersistenciaSQLite)
        
    def inicializar_banco(self, url_script_sql = configuracoes.url_script_geracao_banco_sqlite):
        return super().inicializar_banco(url_script_sql)


class GerenciadorPersistenciaSQL(GerenciadorPersistencia):
    def __init__(self, info_banco: dict=configuracoes.configuracoes_banco_sql()):
        super().__init__(
            info_banco=info_banco,
            classeInterface=InterfacePersistenciaSQL)
        
    def inicializar_banco(self, url_script_sql = configuracoes.url_script_geracao_banco_sql):
        return super().inicializar_banco(url_script_sql)


if __name__ == '__main__':
    print(f'Criando banco SQL com documentos do banco vetorial ({configuracoes.url_banco_vetores})')
    if configuracoes.tipo_persistencia == 'mssql':
        gp = GerenciadorPersistenciaSQL()
    elif configuracoes.tipo_persistencia == 'sqlite':
        gp = GerenciadorPersistenciaSQLite()
    print('-- criando tabelas')
    gp.inicializar_banco()
    url_descritor = os.path.join(configuracoes.url_banco_vetores, 'descritor.json')
    print('-- salvando coleções')
    gp.persistir_dados_colecao(url_descritor_banco_vetorial=url_descritor)
    print('-- salvando documentos')
    gp.persistir_documentos(url_descritor_banco_vetorial=url_descritor)
    print('Banco SQL concluído.\n\n')
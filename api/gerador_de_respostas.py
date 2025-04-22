import json
from torch import cuda
from concurrent.futures import ThreadPoolExecutor
from time import time
import wandb

from api.configuracoes.config_gerais import configuracoes
from api.dados.persistencia import GerenciadorPersistencia
from api.utils.interface_llm import InterfaceLLM, DadosChat
from api.utils.interface_banco_vetores import InterfaceBancoVetorial
from api.utils.reclassificador import Reclassificador
from api.utils.mensagem import MensagemControle, MensagemDados, MensagemErro, MensagemInfo
from api.utils.gerador_prompts import GeradorPrompts
    

class GeradorDeRespostas:
    '''
    Classe cuja função é realizar consulta em um banco de vetores existente e, por meio de uma API de um LLM
    gera uma texto de resposta que condensa as informações resultantes da consulta.
    '''
    def __init__(self,
                 interface_banco_vetorial: InterfaceBancoVetorial,
                 interface_llm: InterfaceLLM,
                 reclassificador: Reclassificador,
                 gerenciador_persistencia:GerenciadorPersistencia,
                 fazer_log:bool=True,
                 device: str=None):
        
        if configuracoes.usar_wandb:
            self.wandb_run = wandb.init(
                project=configuracoes.wandb_nome_projeto,
                entity=configuracoes.wandb_equipe,
                job_type=configuracoes.wandb_tipo_execucao,
                config=configuracoes.sumarizar_configuracoes(),
            )
            self.tabela_log_requisicao = wandb.Table(columns=['pergunta', 'resposta', 'documentos','tempo_consulta', 'tempo_bert', 'resposta_completa_llm','tempo_inicio_resposta', 'tempo_ollama_total'])
        else:
            self.tabela_log_requisicao = None
        self.fazer_log = fazer_log
        self.device = device
        self.executor = ThreadPoolExecutor(max_workers=configuracoes.threadpool_max_workers)

        self.interface_banco_vetorial = interface_banco_vetorial

        self.reestimador = reclassificador
        
        self.interface_llm = interface_llm
        
        self.gerenciador_persistencia = gerenciador_persistencia
        
    def health(self):
        status_code_llm = self.interface_llm.health()
        return json.dumps({
            'status_api': 'Ativo',
            'status_cliente_llm': 'Ativo' if status_code_llm == 200 else 'Inativo'
        })

    async def consultar_documentos_banco_vetores(self, pergunta: str, num_resultados:int=configuracoes.num_documentos_retornados):
        return self.interface_banco_vetorial.consultar_documentos(pergunta, num_resultados)
    
    def formatar_lista_documentos(self, documentos: dict):
        return [
            {
                'id': documentos['ids'][0][idx],
                'score_distancia': 1 - documentos['distances'][0][idx], # Distância do cosseno varia entre 1 e 0
                'metadados': documentos['metadatas'][0][idx],
                'conteudo': documentos['documents'][0][idx]
            } for idx in range(len(documentos['ids'][0]))
        ]

    async def reclassificar_documentos(self, pergunta, texto_documento: str):
        return self.reestimador.reclassificar_documento(pergunta=pergunta, texto_documento=texto_documento)

    async def gerar_resposta(self, dados_chat: DadosChat):
        historico = dados_chat.historico
        pergunta = dados_chat.pergunta
        id_sessao = dados_chat.id_sessao
        id_cliente = dados_chat.id_cliente
        
        if len(pergunta.split(' ')) > 300:
            #AFAZER: decidir se mantém essa limitação. Colocada a princípio para evitar
            #        problema de truncation com o Bert. Ajuda com Prompt Injection?
            yield MensagemErro(
                    descricao='Pergunta com mais de 300 palavras',
                    mensagem='Por motivos de segurança, a pergunta deve ter no máximo 300 palavras. Por favor, reformule o que você deseja perguntar, para ficar dentro desse limite.'
                ).json() + '\n'
            print('CONCLUÍDO POR ERRO: pergunta com mais de 300 palavras.')
            return

        if self.fazer_log: print(f'Gerador de respostas: realizando consulta para "{pergunta}"...')
        yield MensagemControle(
            descricao='Informação de Status',
            dados={'tag':'status', 'conteudo': configuracoes.mensagens_retorno['consulta']}
        ).json() + '\n'
        
        # Recuperando documentos usando o ChromaDB
        marcador_tempo_inicio = time()
        try:
            documentos = await self.consultar_documentos_banco_vetores(pergunta)
            lista_documentos_formatados = self.formatar_lista_documentos(documentos)
        except Exception as excecao:
            print(excecao.__traceback__)
            yield MensagemErro(
                descricao='Falha na Consulta ao Banco Vetorial',
                mensagem=f'Houve um problema na consulta de documentos. Tente mais tarde. (Tipo do erro: {excecao.__class__.__name__})'
            ).json() + '\n'
            return
            
        marcador_tempo_fim = time()
        tempo_recuperacao_documentos = marcador_tempo_fim - marcador_tempo_inicio
        if self.fazer_log: print(f'--- consulta no banco concluída ({tempo_recuperacao_documentos} segundos)')

        # Fazendo re-ranking dos documentos utilizando Bert
        if self.fazer_log: print(f'--- aplicando re-ranking nos documentos utilizando Bert...')
        yield MensagemControle(
            descricao='Informação de Status',
            dados={'tag':'status', 'conteudo': configuracoes.mensagens_retorno['reranking']}
        ).json() + '\n'

        marcador_tempo_inicio = time()
        for documento in lista_documentos_formatados:
            try:
                resposta_estimada = await self.reclassificar_documentos(pergunta, documento['conteudo'])
                documento['score_bert'] = resposta_estimada['score']
                documento['score_ponderado'] = resposta_estimada['score_ponderado']
                documento['resposta_bert'] = resposta_estimada['resposta']
            except Exception as excecao:
                documento['score_bert'] = float('-inf')
                documento['score_ponderado'] = float('-inf')
                documento['resposta_bert'] = 'Resposta não estimada'
                yield MensagemInfo(
                    descricao='Falha na aplicação do BERT',
                    mensagem='Houve erro na aplicação dos valores, mas o processo continuou. Scores atribuídos com menor valor possível'
                ).json() + '\n'

        # reordenando lista com base no score atribuído pelo Bert
        lista_documentos_formatados = sorted(lista_documentos_formatados, key=lambda x: x['score_bert'][0], reverse=True)
        marcador_tempo_fim = time()
        tempo_estimativa_bert = marcador_tempo_fim - marcador_tempo_inicio
        if self.fazer_log: print(f'--- scores atribuídos ({tempo_estimativa_bert} segundos)')
        
        yield MensagemDados(
            descricao='Lista de Documentos Recuperados',
            dados={
                'tag': 'lista-docs-recuperados',
                'conteudo': lista_documentos_formatados
            }
            ).json() + '\n'
        
        # Gerando resposta utilizando a interface do LLM
        if self.fazer_log: print(f'--- gerando resposta com o cliente LLM')
        yield MensagemControle(
            descricao='Informação de Status',
            dados={'tag':'status', 'conteudo': configuracoes.mensagens_retorno['geracao_resposta']}
            ).json() + '\n'
        
        try:
            marcador_idioma = GeradorPrompts.criar_marcador_idioma(pergunta)
            if 'mensagem' in marcador_idioma: pergunta += f''' ({marcador_idioma['mensagem']})'''
            marcador_tempo_inicio = time()
            texto_resposta_llm = ''
            flag_tempo_resposta = False

            prompt_usuario = GeradorPrompts.gerar_prompt_rag(pergunta=pergunta, documentos=[f"{doc[0]['titulo']} - {doc[1]}" for doc in zip(documentos['metadatas'][0], documentos['documents'][0])])

            async for item in self.interface_llm.gerar_resposta_llm_stream(prompt_usuario, historico=historico):
                
                texto_resposta_llm += item['message']['content']
                yield MensagemDados(
                    descricao='Fragmento de Resposta do LLM',
                    dados={
                        'tag': 'frag-resposta-llm',
                        'conteudo': item['message']['content']
                    }
                    ).json() + '\n'
                if not flag_tempo_resposta:
                    flag_tempo_resposta = True
                    tempo_inicio_stream_resposta = time() - marcador_tempo_inicio
                    if self.fazer_log: print(f'----- iniciou retorno da resposta ({tempo_inicio_stream_resposta} segundos)')

            resposta_completa_llm = item
            resposta_completa_llm['message']['content'] = texto_resposta_llm
            marcador_tempo_fim = time()
            tempo_cliente_llm = marcador_tempo_fim - marcador_tempo_inicio
            if self.fazer_log: print(f'--- resposta do Ollama concluída ({tempo_cliente_llm} segundos)')
        except Exception as excecao:
            yield MensagemErro(
                descricao=f'Falha na Geração da Resposta (Ollama offline ou {configuracoes.modelo_llm} não disponível. {excecao.__class__.__name__})',
                mensagem=f'Houve um problema geração de sua resposta. Tente mais tarde. (Tipo do erro: {excecao.__class__.__name__})'
            ).json() + '\n'
            print(f'CONCLUÍDO POR ERRO: Falha na conexão com o LLM. Ollama offline ou {configuracoes.modelo_llm} não disponível. {excecao.__class__.__name__}')
            return
        
        dados_interacao = {
            'pergunta': pergunta,
            'tipo_dispositivo_aplicacao': configuracoes.device,
            'tipo_dispositivo_llm': 'cuda' if cuda.is_available() else 'cpu',
            'documentos': lista_documentos_formatados,
            'tempo_recuperacao_documentos': tempo_recuperacao_documentos,
            'tempo_estimativa_bert': tempo_estimativa_bert,
            'template_system_llm': configuracoes.template_mensagem_system,
            'historico_llm': historico,
            'cliente_llm': configuracoes.cliente_llm,
            'modelo_llm': configuracoes.modelo_llm,
            'tempo_inicio_stream_resposta': tempo_inicio_stream_resposta,
            'tempo_total_llm': tempo_cliente_llm,
            'resposta': texto_resposta_llm,
            'resposta_completa_llm': resposta_completa_llm,
            'id_sessao': id_sessao,
            'id_cliente': id_cliente
        }
        
        # id no índice 0 é o da interação persistida
        ids_persistencia_interacao = self.gerenciador_persistencia.persistir_interacao(dados_interacao=dados_interacao)
        
        # Retornando dados compilados
        msg = MensagemDados(
                descricao='INTERAÇÃO FINALIZADA. Contém Id da interação (primeiro elemento) e das relações dos documentos na interação',
                dados={
                    'tag': 'persistencia-interacao',
                    'conteudo': ids_persistencia_interacao
                }
            ).json()
        
        if self.tabela_log_requisicao:
            self.tabela_log_requisicao.add_data(pergunta, texto_resposta_llm, lista_documentos_formatados, tempo_recuperacao_documentos, tempo_estimativa_bert, resposta_completa_llm, tempo_inicio_stream_resposta, tempo_cliente_llm)
            self.wandb_run.log({"Tabela_Requisicao": self.tabela_log_requisicao})

        yield msg
        if self.fazer_log: print('Concluído')

    async def avaliar_interacao(self, dados_avaliacao: dict):
        try:
            resultado = self.gerenciador_persistencia.persistir_avaliacao(dados_avaliacao=dados_avaliacao)
            if resultado == 1:
                dados_avaliacao['sucesso_avaliacao'] = True
                dados_avaliacao['mensagem_retorno'] = 'Avaliação registrada'
            elif resultado == 0:
                dados_avaliacao['sucesso_avaliacao'] = False
                dados_avaliacao['mensagem_retorno'] = 'Query executada, mas dados não registrados'
            else:
                raise Exception('Mais de uma avaliação registrada?!')
        except Exception as e:
            dados_avaliacao['sucesso_avaliacao'] = False
            dados_avaliacao['mensagem_retorno'] = f'Ocorreu um erro. {e}'

        return MensagemDados(
            descricao='Resultado da requisição de avaliação',
            dados={
                'tag': 'persistencia-avaliacao',
                'conteudo': dados_avaliacao
            }
        ).json()

import torch
from torch import cuda

from concurrent.futures import ThreadPoolExecutor
from time import time
from transformers import BertTokenizer, BertForQuestionAnswering
from typing import Callable

import wandb

from api.configuracoes.config_gerais import configuracoes
from api.utils.utils import InterfaceChroma, InterfaceOllama, DadosChat
from api.utils.mensagem import MensagemControle, MensagemDados, MensagemErro, MensagemInfo
from api.dados.persistencia import GerenciadorPersistenciaSQLite, GerenciadorPersistenciaSQL
    

class GeradorDeRespostas:
    '''
    Classe cuja função é realizar consulta em um banco de vetores existente e, por meio de uma API de um LLM
    gera uma texto de resposta que condensa as informações resultantes da consulta.
    '''
    def __init__(self,
                url_banco_vetores:str=configuracoes.url_banco_vetores,
                colecao_de_documentos:str=configuracoes.nome_colecao_de_documentos,
                funcao_de_embeddings:Callable=None,
                fazer_log:bool=True,
                device: str=None):
        
        if configuracoes.usar_wandb:
            self.wandb_run = wandb.init(
                project=configuracoes.wandb_nome_projeto,
                entity=None, # AFAZER: entender o que isso faz
                job_type=configuracoes.wandb_tipo_execucao,
                config=configuracoes.sumarizar_configuracoes(),
            )
            self.tabela_log_requisicao = wandb.Table(columns=['pergunta', 'resposta', 'documentos','tempo_consulta', 'tempo_bert', 'resposta_completa_llm','tempo_inicio_resposta', 'tempo_ollama_total'])
        else:
            self.tabela_log_requisicao = None

        self.device = device
        self.executor = ThreadPoolExecutor(max_workers=configuracoes.threadpool_max_workers)
        
        if fazer_log: print(f'-- Gerador de respostas em inicialização (device={self.device})...')

        self.interface_chromadb = InterfaceChroma(url_banco_vetores, colecao_de_documentos, funcao_de_embeddings, fazer_log)

        # Carregando modelo e tokenizador pre-treinados
        # optou-se por não usar pipeline, por ser mais lento que usar o modelo diretamente
        if fazer_log: print(f'--- preparando modelo e tokenizador do Bert (usando {configuracoes.embedding_squad_portuguese})...')
        self.modelo_bert_qa = BertForQuestionAnswering.from_pretrained(configuracoes.embedding_squad_portuguese).to(self.device)
        self.tokenizador_bert = BertTokenizer.from_pretrained(configuracoes.embedding_squad_portuguese, device=self.device)

        if fazer_log: print(f'--- preparando o Ollama (usando {configuracoes.modelo_llm})...')
        self.interface_ollama = InterfaceOllama(url_ollama=configuracoes.url_llm, nome_modelo=configuracoes.modelo_llm)

        tipo_persistencia = configuracoes.configuracoes_ambiente()['tipo_persistencia']
        if fazer_log: print(f'--- configurando persistência de dados de interação (usando {tipo_persistencia})...')
        if tipo_persistencia == 'sqlite': self.gerenciador_persistencia = GerenciadorPersistenciaSQLite()
        elif tipo_persistencia == 'mssql': self.gerenciador_persistencia = GerenciadorPersistenciaSQL()

    async def consultar_documentos_banco_vetores(self, pergunta: str, num_resultados:int=configuracoes.num_documentos_retornados):
        return self.interface_chromadb.consultar_documentos(pergunta, num_resultados)
    
    def formatar_lista_documentos(self, documentos: dict):
        return [
            {
                'id': documentos['ids'][0][idx],
                'score_distancia': 1 - documentos['distances'][0][idx], # Distância do cosseno varia entre 1 e 0
                'metadados': documentos['metadatas'][0][idx],
                'conteudo': documentos['documents'][0][idx]
            } for idx in range(len(documentos['ids'][0]))
        ]

    async def estimar_resposta(self, pergunta, texto_documento: str):
        inputs = self.tokenizador_bert.encode_plus(
            pergunta,
            texto_documento,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )

        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        
        with torch.no_grad():
            outputs = self.modelo_bert_qa(**inputs)

        # AFAZER: Avaliar se score ponderado faz sentido
        # Extraindo os logits como tensores
        logits_inicio = outputs.start_logits
        logits_fim = outputs.end_logits

        # Obtenção dos logits positivos
        logits_inicio_positivos = logits_inicio[0][logits_inicio[0] > 0]
        logits_fim_positivos = logits_fim[0][logits_fim[0] > 0]

        # Média dos logits positivos
        media_logits_inicio_positivos = logits_inicio_positivos.mean().item() if logits_inicio_positivos.numel() > 0 else 0
        media_logits_fim_positivos = logits_fim_positivos.mean().item() if logits_fim_positivos.numel() > 0 else 0

        # Obtendo os índices e valores dos melhores logits
        indice_melhor_logit_inicio = logits_inicio[0].argmax().item()
        melhor_logit_inicio = logits_inicio[0][indice_melhor_logit_inicio].item()

        indice_melhor_logit_fim = logits_fim[0].argmax().item()
        melhor_logit_fim = logits_fim[0][indice_melhor_logit_fim].item()

        # Calcula media_logits_positivos
        media_logits_positivos = (media_logits_inicio_positivos + media_logits_fim_positivos) / 2

        # scores em formato float para serialização com JSON
        score_soma_logits = float(melhor_logit_inicio + melhor_logit_fim)
        score_ponderado = float(score_soma_logits * media_logits_positivos)

        # calculando score estimado
        start_logits_softmax = torch.softmax(logits_inicio, dim=-1)
        end_logits_softmax = torch.softmax(logits_fim, dim=-1)
        score_estimado = float(torch.max(start_logits_softmax).item() * torch.max(end_logits_softmax).item())

        # score: soma do melhor Logit inicial com o melhor logit final
        # score_estimado: multiplicação do softmax dos logits de inicio pelo dos logits de fim
        # -- (manter somente se a performance do score do Bert pelo pipeline ficar lenta)
        # score_ponderado: score ponderado pela média dos logits de inicio e fim, só quando positivos 
        # -- (quanto mais logits positivos, mais o documento tem melhor avaliação)

        tokens_resposta = inputs['input_ids'][0][indice_melhor_logit_inicio:indice_melhor_logit_fim + 1]
        resposta = self.tokenizador_bert.decode(tokens_resposta, skip_special_tokens=True)
        
        return {
            'resposta': resposta,
            'score': (score_estimado, score_soma_logits),
            'score_ponderado': score_ponderado
        }

    async def consultar(self, dados_chat: DadosChat, fazer_log:bool=True):
        historico = dados_chat.historico
        pergunta = dados_chat.pergunta
        
        if len(pergunta.split(' ')) > 300:
            #AFAZER: decidir se mantém essa limitação. Colocada a princípio para evitar
            #        problema de truncation com o Bert. Ajuda com Prompt Injection?
            yield MensagemErro(
                    descricao='Pergunta com mais de 300 palavras',
                    mensagem='Por motivos de segurança, a pergunta deve ter no máximo 300 palavras. Por favor, reformule o que você deseja perguntar, para ficar dentro desse limite.'
                ).json() + '\n'
            print('CONCLUÍDO POR ERRO: pergunta com mais de 300 palavras.')
            return

        if fazer_log: print(f'Gerador de respostas: realizando consulta para "{pergunta}"...')
        yield MensagemControle(
            descricao='Informação de Status',
            dados={'tag':'status', 'conteudo':'Consultando fontes'}
        ).json() + '\n'
        
        # Recuperando documentos usando o ChromaDB
        marcador_tempo_inicio = time()
        try:
            documentos = await self.consultar_documentos_banco_vetores(pergunta)
            lista_documentos = self.formatar_lista_documentos(documentos)
        except Exception as excecao:
            print(excecao.__traceback__)
            yield MensagemErro(
                descricao='Falha na Consulta ao Banco Vetorial',
                mensagem=f'Houve um problema na consulta de documentos. Tente mais tarde. (Tipo do erro: {excecao.__class__.__name__})'
            ).json() + '\n'
            return
            
        marcador_tempo_fim = time()
        tempo_recuperacao_documentos = marcador_tempo_fim - marcador_tempo_inicio
        if fazer_log: print(f'--- consulta no banco concluída ({tempo_recuperacao_documentos} segundos)')

        # Fazendo re-ranking dos documentos utilizando Bert
        if fazer_log: print(f'--- aplicando re-ranking nos documentos utilizando Bert...')
        yield MensagemControle(
            descricao='Informação de Status',
            dados={'tag':'status', 'conteudo':'Analisando resultados'}
        ).json() + '\n'

        marcador_tempo_inicio = time()
        for documento in lista_documentos:
            try:
                resposta_estimada = await self.estimar_resposta(pergunta, documento['conteudo'])
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
        lista_documentos = sorted(lista_documentos, key=lambda x: x['score_bert'][0], reverse=True)
        marcador_tempo_fim = time()
        tempo_estimativa_bert = marcador_tempo_fim - marcador_tempo_inicio
        if fazer_log: print(f'--- scores atribuídos ({tempo_estimativa_bert} segundos)')
        
        yield MensagemDados(
            descricao='Lista de Documentos Recuperados',
            dados={
                'tag': 'lista-docs-recuperados',
                'conteudo': lista_documentos
            }
            ).json() + '\n'
        
        # Gerando resposta utilizando o Ollama
        if fazer_log: print(f'--- gerando resposta com o cliente LLM')
        yield MensagemControle(
            descricao='Informação de Status',
            dados={'tag':'status', 'conteudo':'Gerando resposta'}
            ).json() + '\n'
        
        try:
            marcador_tempo_inicio = time()
            texto_resposta_llm = ''
            flag_tempo_resposta = False
            async for item in self.interface_ollama.gerar_resposta_llm(
                        pergunta=pergunta,
                        # Inclui o título dos documentos no prompt do LLM
                        documentos=[f"{doc[0]['titulo']} - {doc[1]}" for doc in zip(documentos['metadatas'][0], documentos['documents'][0])],
                        historico=historico):
                
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
                    if fazer_log: print(f'----- iniciou retorno da resposta ({tempo_inicio_stream_resposta} segundos)')

            resposta_completa_llm = item
            resposta_completa_llm['message']['content'] = texto_resposta_llm
            marcador_tempo_fim = time()
            tempo_cliente_llm = marcador_tempo_fim - marcador_tempo_inicio
            if fazer_log: print(f'--- resposta do Ollama concluída ({tempo_cliente_llm} segundos)')
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
            'documentos': lista_documentos,
            'tempo_recuperacao_documentos': tempo_recuperacao_documentos,
            'tempo_estimativa_bert': tempo_estimativa_bert,
            'template_system_llm': configuracoes.template_mensagem_system,
            'historico_llm': historico,
            'cliente_llm': configuracoes.cliente_llm,
            'modelo_llm': configuracoes.modelo_llm,
            'tempo_inicio_stream_resposta': tempo_inicio_stream_resposta,
            'tempo_total_llm': tempo_cliente_llm,
            'resposta': texto_resposta_llm,
            'resposta_completa_llm': resposta_completa_llm
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
            self.tabela_log_requisicao.add_data(pergunta, texto_resposta_llm, lista_documentos, tempo_recuperacao_documentos, tempo_estimativa_bert, resposta_completa_llm, tempo_inicio_stream_resposta, tempo_cliente_llm)
            self.wandb_run.log({"Tabela_Requisicao": self.tabela_log_requisicao})

        yield msg
        print('Concluído')

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

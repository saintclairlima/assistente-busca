print('Inicializando a estrutura da API...\nImportando as bibliotecas...')
import uuid
from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from sentence_transformers import SentenceTransformer
from starlette.middleware.cors import CORSMiddleware

from api.configuracoes.config_gerais import configuracoes
from api.gerador_de_respostas import GeradorDeRespostas
from api.utils.interface_banco_vetores import FuncaoEmbeddings, InterfaceChroma
from api.utils.interface_llm import DadosChat, InterfaceOllama
from api.dados.persistencia import GerenciadorPersistenciaSQL, GerenciadorPersistenciaSQLite
from api.utils.reclassificador import ReclassificadorBert
from api.utils.classificador_de_intencao import ClassificadorIntencaoEmbeddings

classificador_de_intencao = ClassificadorIntencaoEmbeddings()

print('Instanciando a api (FastAPI)...')
controller = FastAPI()
controller.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Allow all origins
    allow_credentials=True,
    allow_methods=['*'],  # Allow all methods
    allow_headers=['*'],  # Allow all headers
)

fazer_log = True

print(f'Criando GeradorDeRespostas (usando {configuracoes.modelo_funcao_de_embeddings} - device={configuracoes.device})...')
print(f'--- criando a função de embeddings do ChromaDB com {configuracoes.modelo_funcao_de_embeddings} (device={configuracoes.device})...')
funcao_de_embeddings = FuncaoEmbeddings(
    nome_modelo=configuracoes.modelo_funcao_de_embeddings,
    tipo_modelo=SentenceTransformer,
    device=configuracoes.device)

interface_banco_vetorial = InterfaceChroma(
    url_banco_vetores=configuracoes.url_banco_vetores,
    colecao_de_documentos=configuracoes.nome_colecao_de_documentos,
    funcao_de_embeddings=funcao_de_embeddings,
    fazer_log=fazer_log)

reclassificador_bert = ReclassificadorBert(device=configuracoes.device, fazer_log=fazer_log)

if fazer_log: print(f'--- preparando o Ollama (usando {configuracoes.modelo_llm})...')
interface_llm = InterfaceOllama(url_ollama=configuracoes.url_llm, nome_modelo=configuracoes.modelo_llm)

tipo_persistencia = configuracoes.configuracoes_ambiente()['tipo_persistencia']
if fazer_log: print(f'--- configurando persistência de dados de interação (usando {tipo_persistencia})...')
if tipo_persistencia == 'sqlite': gerenciador_persistencia = GerenciadorPersistenciaSQLite()
elif tipo_persistencia == 'mssql': gerenciador_persistencia = GerenciadorPersistenciaSQL()

gerador_de_respostas = GeradorDeRespostas(
    interface_banco_vetorial=interface_banco_vetorial,
    reclassificador=reclassificador_bert,
    interface_llm=interface_llm,
    gerenciador_persistencia=gerenciador_persistencia,
    device=configuracoes.device,
    fazer_log=fazer_log)

print('Definindo as rotas')

def recuperar_pagina_chat(request: Request, url_redirec: str = Query(None)):    
    with open('web/chat.html', 'r', encoding='utf-8') as arquivo: conteudo_html = arquivo.read()
    # AFAZER: considerar se manter esse elemento faz sentido. Só é utilizado para uso de testes com o ngrok, no colab
    if url_redirec:
        configuracoes.tags_substituicao_html['TAG_INSERCAO_URL_HOST'] = url_redirec
    
    # substituindo as tags dentro do HTML, para maior controle
    for tag, valor in configuracoes.tags_substituicao_html.items():
        conteudo_html = conteudo_html.replace(tag, valor)
    conteudo_html = conteudo_html.replace('TAG_INSERCAO_UUID_SESSAO', str(uuid.uuid4()))
    
    response = HTMLResponse(content=conteudo_html, status_code=200)
    if not request.cookies.get("idCliente"):
        response.set_cookie(key="idCliente", value=str(uuid.uuid4()))
    
    return response

@controller.get('/chat/health')
async def chat_health():
    return gerador_de_respostas.health()

@controller.get('/')
async def raiz(request: Request, url_redirec: str = Query(None)):
    return recuperar_pagina_chat(request=request, url_redirec=url_redirec)

@controller.get('/chat/')
async def pagina_chat(request: Request, url_redirec: str = Query(None)):
    return recuperar_pagina_chat(request=request, url_redirec=url_redirec)

@controller.post('/chat/enviar-pergunta/')
async def gerar_resposta(dadosRecebidos: DadosChat):
    dadosRecebidos.intencao = classificador_de_intencao.classificar_intencao(dadosRecebidos.pergunta)
    return StreamingResponse(
        gerador_de_respostas.gerar_resposta(dadosRecebidos),
        media_type='text/plain'
    )

@controller.post('/chat/avaliar-interacao/')
async def gerar_resposta(dadosRecebidos: dict):
    return await gerador_de_respostas.avaliar_interacao(dadosRecebidos)

@controller.get('/chat/documento')
async def pagina_chat(url_documento: str = Query(None)):
    with open(f'api/dados/{url_documento}', 'r', encoding='utf-8') as arquivo: conteudo_html = arquivo.read()
    return HTMLResponse(content=conteudo_html, status_code=200)

@controller.get('/web/img/favicon/favicon.ico')
async def favicon(): return FileResponse('web/img/favicon/favicon.ico')

@controller.get('/web/img/favicon/favicon.svg')
async def favicon(): return FileResponse('web/img/favicon/favicon.svg')

@controller.get('/web/img/favicon/favicon-48x48.png')
async def favicon(): return FileResponse('web/img/favicon/favicon-48x48.png')

@controller.get('/web/img/favicon/apple-touch-icon.png')
async def favicon(): return FileResponse('web/img/favicon/apple-touch-icon.png')

@controller.get('/web/img/favicon/site.webmanifest')
async def favicon(): return FileResponse('web/img/favicon/site.webmanifest')

@controller.get('/web/img/favicon/web-app-manifest-192x192.png')
async def favicon(): return FileResponse('web/img/favicon/web-app-manifest-192x192.png')

@controller.get('/web/img/favicon/web-app-manifest-512x512.png')
async def favicon(): return FileResponse('web/img/favicon/web-app-manifest-512x512.png')

@controller.get('/web/img/Assistente_.png')
async def assistente_(): return FileResponse('web/img/Assistente_.png')

@controller.get('/web/img/Assistente.png')
async def assistente(): return FileResponse('web/img/Assistente.png')

@controller.get('/web/img/logo_al.png')
async def logo(): return FileResponse('web/img/logo_al.png')

@controller.get('/web/markdown.js')
async def markdown(): return FileResponse('web/markdown.js')

@controller.get('/web/chat.js')
async def chat_js(): return FileResponse('web/chat.js')

@controller.get('/web/chat.css')
async def chat_css(): return FileResponse('web/chat.css')

@controller.get('/catalogo')
async def catalogo():
    with open(f'web/catalogo-atividades.html', 'r', encoding='utf-8') as arquivo: conteudo_html = arquivo.read()
    return HTMLResponse(content=conteudo_html, status_code=200)

print('API inicializada')
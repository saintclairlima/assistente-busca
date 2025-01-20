print('Inicializando a estrutura da API...\nImportando as bibliotecas...')
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from sentence_transformers import SentenceTransformer
from starlette.middleware.cors import CORSMiddleware

from api.configuracoes.config_gerais import configuracoes
from api.gerador_de_respostas import GeradorDeRespostas
from api.utils.utils import FuncaoEmbeddings, DadosChat

print('Instanciando a api (FastAPI)...')
controller = FastAPI()
controller.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Allow all origins
    allow_credentials=True,
    allow_methods=['*'],  # Allow all methods
    allow_headers=['*'],  # Allow all headers
)

print(f'Criando GeradorDeRespostas (usando {configuracoes.modelo_funcao_de_embeddings} - device={configuracoes.device})...')
funcao_de_embeddings = FuncaoEmbeddings(nome_modelo=configuracoes.modelo_funcao_de_embeddings, tipo_modelo=SentenceTransformer, device=configuracoes.device)
gerador_de_respostas = GeradorDeRespostas(funcao_de_embeddings=funcao_de_embeddings, url_banco_vetores=configuracoes.url_banco_vetores, device=configuracoes.device)

print('Definindo as rotas')


@controller.get('/chat/')
async def pagina_chat(url_redirec: str = Query(None)):
    with open('web/chat.html', 'r', encoding='utf-8') as arquivo: conteudo_html = arquivo.read()
    # AFAZER: considerar se manter esse elemento faz sentido. Só é utilizado para uso de testes com o ngrok, no colab
    if url_redirec:
        configuracoes.tags_substituicao_html['TAG_INSERCAO_URL_HOST'] = url_redirec
        
    # substituindo as tags dentro do HTML, para maior controle
    for tag, valor in configuracoes.tags_substituicao_html.items():
        conteudo_html = conteudo_html.replace(tag, valor)
    return HTMLResponse(content=conteudo_html, status_code=200)

@controller.post('/chat/enviar-pergunta/')
async def gerar_resposta(dadosRecebidos: DadosChat):
    return StreamingResponse(gerador_de_respostas.consultar(dadosRecebidos), media_type='text/plain')

@controller.post('/chat/avaliar-interacao/')
async def gerar_resposta(dadosRecebidos: dict):
    return await gerador_de_respostas.avaliar_interacao(dadosRecebidos)

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

print('API inicializada')
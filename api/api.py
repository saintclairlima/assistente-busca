print('Inicializando a estrutura da API...\nImportando as bibliotecas...')
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from sentence_transformers import SentenceTransformer
from starlette.middleware.cors import CORSMiddleware

from api.environment.environment import environment
from api.gerador_de_respostas import GeradorDeRespostas, DadosChat
from api.utils.utils import FuncaoEmbeddings

print('Instanciando a api (FastAPI)...')
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Allow all origins
    allow_credentials=True,
    allow_methods=['*'],  # Allow all methods
    allow_headers=['*'],  # Allow all headers
)

print(f'Criando GeradorDeRespostas (usando {environment.MODELO_DE_EMBEDDINGS} - device={environment.DEVICE})...')
funcao_de_embeddings = FuncaoEmbeddings(nome_modelo=environment.MODELO_DE_EMBEDDINGS, tipo_modelo=SentenceTransformer, device=environment.DEVICE)
gerador_de_respostas = GeradorDeRespostas(funcao_de_embeddings=funcao_de_embeddings, url_banco_vetores=environment.URL_BANCO_VETORES, device=environment.DEVICE)

print('Definindo as rotas')

@app.post('/chat/enviar_pergunta/')
async def gerar_resposta(dadosRecebidos: DadosChat):
    return StreamingResponse(gerador_de_respostas.consultar(dadosRecebidos), media_type='text/plain')


@app.get('/chat/')
async def pagina_chat(url_redirec: str = Query(None)):
    with open('web/chat.html', 'r', encoding='utf-8') as arquivo: conteudo_html = arquivo.read()
    # AFAZER: considerar se manter esse elemento faz sentido. Só é utilizado para uso de testes com o ngrok, no colab
    if url_redirec:
        environment.TAGS_SUBSTITUICAO_HTML['TAG_INSERCAO_URL_HOST'] = url_redirec
        
    # substituindo as tags dentro do HTML, para maior controle
    for tag, valor in environment.TAGS_SUBSTITUICAO_HTML.items():
        conteudo_html = conteudo_html.replace(tag, valor)
    return HTMLResponse(content=conteudo_html, status_code=200)

@app.get('/web/img/favicon/favicon.ico')
async def favicon(): return FileResponse('web/img/favicon/favicon.ico')

@app.get('/web/img/favicon/favicon.svg')
async def favicon(): return FileResponse('web/img/favicon/favicon.svg')

@app.get('/web/img/favicon/favicon-48x48.png')
async def favicon(): return FileResponse('web/img/favicon/favicon-48x48.png')

@app.get('/web/img/favicon/apple-touch-icon.png')
async def favicon(): return FileResponse('web/img/favicon/apple-touch-icon.png')

@app.get('/web/img/favicon/site.webmanifest')
async def favicon(): return FileResponse('web/img/favicon/site.webmanifest')

@app.get('/web/img/Assistente_.png')
async def assistente_(): return FileResponse('web/img/Assistente_.png')

@app.get('/web/img/Assistente.png')
async def assistente(): return FileResponse('web/img/Assistente.png')

@app.get('/web/img/logo_al.png')
async def logo(): return FileResponse('web/img/logo_al.png')

@app.get('/web/markdown.js')
async def markdown(): return FileResponse('web/markdown.js')

print('API inicializada')
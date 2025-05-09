from chromadb import chromadb
from api.utils.interface_banco_vetores import FuncaoEmbeddingsGeneric
import uuid
import tensorflow_hub as hub

cliente_chroma = chromadb.PersistentClient(path='api/dados/bancos_vetores/banco_assistente')
col_bge = cliente_chroma.get_collection(name='documentos_rh_bge_m3')
dados_bge = col_bge.get()

print(dados_bge['metadatas'][0])


funcao_customizada = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
funcao = FuncaoEmbeddingsGeneric(funcao=funcao_customizada)


#col_use = cliente_chroma.get_collection(name='documentos_rh_univ_sent_enc')
col_use = cliente_chroma.create_collection(name='documentos_rh_univ_sent_enc', embedding_function=funcao, metadata={'hnsw:space': 'cosine', 'uuid': str(uuid.uuid4())})

documentos = dados_bge['documents']
metadatas = dados_bge['metadatas']
qtd_docs = len(documentos)

for idx in range(qtd_docs):
    print(f'\r>>> Incluindo documento {idx+1} de {qtd_docs}', end='')
    doc_texto = documentos[idx]
    metadata = metadatas[idx]

    uuid_doc = str(uuid.uuid4())
    metadata['id'] = uuid_doc

    col_use.add(
        documents=[doc_texto],
        ids=[uuid_doc],
        metadatas=[metadata],
    )
print('\n-- Coleção concluída')
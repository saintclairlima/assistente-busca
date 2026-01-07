REM echo "Criando ambiente virtual python..."
REM python -m venv chat-env
REM chat-env\Scripts\activate
REM echo "\n\n\n"

echo "Preparando os arquivos necessários..."
copy api\.env.TEMPLATE api\.env
copy api\configuracoes\arq_conf_template.json api\configuracoes\arq_conf.json

echo "Instalando dependências..."
python -m pip install --upgrade pip
REM  pip install torch --index-url https://download.pytorch.org/whl/cpu                   # Ambiente com CPU
REM  pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cu126   # Ambiente com CUDA 12.6
pip install -r requirements.txt
echo "\n\n\n"

echo "Criando banco vetorial a partir dos documentos..."
python -m api.dados.gerenciador_banco_vetores --nome_banco_vetores banco_assistente --lista_colecoes "['documentos_rh_bge_m3']" --lista_nomes_modelos_embeddings "['BAAI/bge-m3']" --comprimento_max_fragmento 300

echo "Criando banco SQLite para persistência das interações..."
python -m api.dados.persistencia
echo "\n\n\n"

echo "Concluído!"

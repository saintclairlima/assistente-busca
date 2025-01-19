echo "Preparando os arquivos necessários..."
cp api/.env.TEMPLATE api/.env
unzip api/dados/bancos_vetores/bancos_vetores.zip -d api/dados/bancos_vetores
rm -R api/dados/bancos_vetores/banco_vetores_alrn
rm -R api/dados/bancos_vetores/banco_vetores_regimento_resolucoes_rh
rm -R api/dados/bancos_vetores/resultados_testes

echo "Criando ambiente virtual python..."
python3 -m venv chat-env
source chat-env/bin/activate

echo "Instalando dependências..."
pip install -r requirements.txt

echo "Criando banco SQLite para persistência das interações..."
python3 -m api.dados.persistencia

echo "Concluído!"

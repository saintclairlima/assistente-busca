echo "Preparando os arquivos necessários..."
cp api\.env.TEMPLATE api\.env
tar -xf .\bancos_vetores.zip
rmdir /s /q api\dados\bancos_vetores\banco_vetores_alrn
rmdir /s /q api\dados\bancos_vetores\banco_vetores_regimento_resolucoes_rh
rmdir /s /q api\dados\bancos_vetores\resultados_testes

echo "Criando ambiente virtual python..."
python -m venv chat-env
source chat-env\Script\activate

echo "Instalando dependências..."
pip install -r requirements.txt

echo "Criando banco SQLite para persistência das interações..."
python -m api.dados.persistencia

echo "Concluído!"

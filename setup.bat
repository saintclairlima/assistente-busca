echo "Preparando os arquivos necessários..."
copy api\.env.TEMPLATE api\.env
copy api\configuracoes\arq_conf_template.json api\configuracoes\arq_conf.json
tar -xf .\api\dados\bancos_vetores\bancos_vetores.zip -C .\api\dados\bancos_vetores
rmdir /s /q api\dados\bancos_vetores\banco_vetores_alrn
rmdir /s /q api\dados\bancos_vetores\banco_vetores_regimento_resolucoes_rh
rmdir /s /q api\dados\bancos_vetores\resultados_testes
echo "\n\n\n"

echo "Criando ambiente virtual python..."
python -m venv chat-env
chat-env\Scripts\activate
echo "\n\n\n"

echo "Instalando dependências..."
pip install -r requirements.txt
echo "\n\n\n"

echo "Criando banco SQLite para persistência das interações..."
python -m api.dados.persistencia
echo "\n\n\n"

echo "Concluído!"

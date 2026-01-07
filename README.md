# Assistente de Busca

## Introdução
O Assistente de Busca é uma aplicação de busca de conteúdo em documentos, com sumarização automática de conteúdo. Trata-se de um projeto desenvolvido, sob a direção da Diretoria de Gestão Tecnológica e Inovação (DGTI) da Assembleia Legislativa do Rio Grande do Norte (Alern), com o intuito de ser uma ferramenta interativa de busca de conteúdo dinâmico sob demanda.

A aplicação utiliza uma estrutura de Geração de Texto Aumentada por Recuperação de Documentos ([Retrieval-Augmented Generation - RAG](https://arxiv.org/pdf/2005.11401)), utilizando perguntas dos usuários como termos de busca, para recuperação de documentos (que contêm conteúdo relativo à busca) e, com base no conteúdo recuperado, geração de uma resposta ou sumário, lançando mão de um Large Language Model (LLM).

A implementação de teste/demonstração - cujo conteúdo é incluso nesse repositório - utiliza um conjunto de dados cujo conteúdo é (1) O Regime Jurídico dos Servidores do RN, (2) Regimento Interno da Alern e (3) um conjunto de diversas resoluções da Alern, mais voltadas para a Gestão de Pessoal.

## Modelo LLM
A criação da resposta final ao usuário depende da utilização de um Grande Modelo de Linguagem (LLM) para geração do conteúdo a ser apresentado. O assistente foi desenhado para ser independente de modelos específicos, de forma a ser mais flexível.

Como forma de facilitar o processo de adaptação, mudanças e atualização, optamos por adotar um cliente LLM chamado Ollama. Mais informações a respeito em https://ollama.com/.

### Instalando o Ollama
#### Linux
* No terminal, baixe e execute o script de instalação:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```
#### Windows
* Acesse a página de download do Ollama no link https://ollama.com/download/windows e faça o download do instalador.
* Execute o instalador e siga as instruções em tela

### Inicializando o Ollama como API
Para inicializar o Ollama, basta executar
```
ollama serve
```

Caso `OLLAMA_DEBUG` esteja configurado como `true` (ver abaixo) é feito um log com as configurações de inicialização do Ollama.

É necessário que o Ollama esteja executando para realizar a adição de modelos.

**Obs**: No Windows, logo após a instalação do Ollama, ele inicializa em segundo plano. Se for o caso de se desejar acompanhar os *logs* da aplicação em tela, é necessário encerrar a execução de segundo plano e inicializá-la manualmente em uma sessão do prompt/Powershell.

### Adicionando os modelos ao Ollama
No projeto, utilizamos como modelo principal o `Llama3.1`, mas outros modelos são disponíveis para download (como o `phi3.5`, por exemplo).
Para inclusão do modelo, tanto no Windos como no Linux, por meio do terminal/prompt/Powershell, executa-se:

```
ollama pull <nome do modelo>
```
Em nosso caso:
```
ollama pull llama3.1
```
Após a inclusão do modelo no Ollama, pode-se testar se tudo ocorreu corretamente executando o modelo direto no terminal/prompt/Powershell:
```
ollama run <nome do modelo>
```
Em nosso caso:
```
ollama run llama3.1
```

### Configurações de Ambiente
De forma a aceitar requisições concorrentes, o Ollama precisa ter alguns parâmetros configurados adequadamente. Para isso, é necessário estabelecer algumas variáveis de ambiente a serem utilizadas por ele, a saber:
* OLLAMA_NUM_PARALLEL
* OLLAMA_MAX_LOADED_MODELS
* OLLAMA_MAX_QUEUE
* OLLAMA_CONTEXT_LENGTH

De acordo com a documentação (ver https://github.com/ollama/ollama/blob/main/docs/faq.md), cada uma das variáveis faz o seguinte:
* `OLLAMA_MAX_LOADED_MODELS` - O número máximo de modelos que podem ser carregados simultaneamente, desde que caibam na memória disponível. O padrão é 3 * o número de GPUs ou 3 para inferência via CPU.
* `OLLAMA_NUM_PARALLEL` - O número máximo de solicitações paralelas que cada modelo processará ao mesmo tempo. O padrão irá selecionar automaticamente 4 ou 1 dependendo da memória disponível.
* `OLLAMA_MAX_QUEUE` - O número máximo de solicitações que Ollama irá enfileirar quando estiver ocupado, antes de rejeitar solicitações adicionais. O padrão é 512.
* `OLLAMA_CONTEXT_LENGTH` - O tamanho máximo da "janela de contexto" utilizado pelo Ollama. Todo prompt que ultrapassar a quantidade de tokens do tamanho máximo do contexto será truncado, de forma que parte de seu conteúdo será descartado. O valor padrão é 4096 tokens. Não é bom que o tamanho seja muito pequeno, mas deixá-lo desnecessariamente grande pode deixar as execuções muito pesadas, dependendo da quantidade de memórias disponível.

Outra variável de interesse pode ser `OLLAMA_DEBUG` (true para ativar debug), que mantém um log das atividades internas do Ollama em um terminal, após sua inicialização.

Assim, definimos as variáveis de ambiente semelhante ao que segue.

#### Linux
```
export OLLAMA_NUM_PARALLEL=5
export OLLAMA_MAX_LOADED_MODELS=5
export OLLAMA_MAX_QUEUE=512
export OLLAMA_DEBUG='true'
```
#### Windows (Powershell)
```
$env:OLLAMA_NUM_PARALLEL=5;$env:OLLAMA_MAX_LOADED_MODELS=5;$env:OLLAMA_MAX_QUEUE=512;$env:OLLAMA_DEBUG='true'
```
#### Windows (Prompt)
```
set OLLAMA_NUM_PARALLEL=5
set OLLAMA_MAX_LOADED_MODELS=5
set OLLAMA_MAX_QUEUE=512
set OLLAMA_DEBUG='true'
```

## Python: Instalação e Configuração
### Instalando Python
#### Windows
Instale Python e o gerenciador de pacotes do Python `pip`.
* Acesse a página de download do instalador (https://www.python.org/downloads/).
* Até 13/11/2024 a versão mais recente do Python não tem uma versão do `torch` disponível. É necessário utilizar a versão 3.12 do Python.
* Execute o instalador, seguindo as orientações em tela.
* _OBS:_ O instalador Windows já oferece a opção de incluir o `pip` durante a instalação do Python.

#### Linux
Utilize o gerenciador de pacotes da sua distribuição para instalar.

```
sudo apt install python3
sudo apt install pip
```
### OPCIONAL: Utilizando um ambiente virtual Python
Após a instalação do Python, você pode optar por criar um ambiente Python específico para a instalação dos pacotes necessários a este projeto. Assim, você pode utilizar a mesma instalação do Python em outros projetos, com outras versões de bibliotecas diferentes deste.

Apesar de não ser obrigatório, é aconselhado, para fins de organização, apenas, a realização desse procedimento.

#### Criando o ambiente virtual
Dentro da pasta do projeto (ver mais abaixo), basta executar o seguinte para realizar a criação do ambiente:

```
python -m venv <nome-do-ambiente-à-sua-escolha>
```

No nosso caso, para fins de conveniência, utilizamos `chat-env` como nome do modelo (o controle de versão está configurado para ignorar esses arquivos, como se pode ver no arquivo `.gitignore` - ver mais abaixo).

#### Ativando o ambiente virtual
Após criar o ambiente virtual, é necessário ativá-lo. Para isso, acessa a pasta do projeto a partir do terminal/prompt/Powershell.

##### Linux
```
source ./<nome-do-ambiente>/bin/activate
```
No nosso caso:
```
source ./chat-env/bin/activate
```

##### Windows
```
./<nome-do-ambiente>/Scripts/activate
```
No nosso caso:
```
source ./chat-env/Scripts/activate
```

#### Desativando o ambiente virtual
```
deactivate
```

## Copiando e Configurando o Projeto
### Baixando os arquivos do projeto
Utilize o git para baixar o repositório

```git
git clone https://github.com/saintclairlima/assistente-busca.git

cd ./assistente-busca
```

O `.gitignore` do repositório está configurado para ignorar a pasta com os arquivos do ambiente virtual Python, de forma a não incluí-la no controle de versão. O nome de referência da dita pasta está como `chat-env`, sendo o motivo pelo qual sugerimos nomear o ambiente virtual como `chat-env`.

### Instalando as dependências

Dependendo do dispositivo de processamento (CPU/GPU) a ser utilizado, é necessário instalar uma versão específica do `torch`. Para utilização com CPUs, recomenda-se utilizar o comando seguinte para instalação:

```
pip install torch --index-url https://download.pytorch.org/whl/cpu
```
Em ambientes com placa de vídeo com suporte a CUDA, deve-se alterar para buscar a versão adequada to `torch` com o suporte à versão do CUDA que a placa utiliza.

Por meio do comando
```
 nvidia-smi
 ```
 é possível identificar as características da placa de vídeo persente na máquina, normalemtne sob o rótulo `CUDA Version`.

É possível acessar https://pytorch.org/get-started/locally/ e se obter o comando de instalação adequado, dependendo da versão do CUDA da placa de vídeo.

No caso da versão 12.6 do CUDA, a página resulta em:

```
pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cu126
```

Após esses ajustes, basta instalar os requisitos gerais com:

```
pip install -r requirements.txt
```
É importante instalar o `torch` isoladamente, antes da de instalar os pacotes no arquivo de requirements, de forma a evitar que durante a instalação de outros pacotes a versão do `torch` seja sobreescrita.

**Obs**: Em alguns casos, há problema de conflito entre a versão do `Numpy` nos requisitos (2.x) e a biblioteca `transformers`. Sendo este o caso, basta instalar uma versão 1.x do `Numpy`.

**CUIDADO**: Em ambientes com GPU garanta que sua placa gráfica tem os requisitos mínimos para executar ao mesmo tempo a API Ollama e os recursos do Assistente de Busca. Caso não seja suficiente para execuçaõ mútua, o Ollama passará a utilizar a CPU, deixando o processo de geraça~ode resposta lento. Priorize o uso da GPU pelo Ollama.

### Arquivos de ambiente e configuração
Antes da execução, é necessário criar um arquivo `.env`, na pasta `/api`, com um conteúdo conforme o arquivo `.TEMPLATE`.

#### Arquivo `.env`
Na pasta `/api` do projeto, crie um arquivo `.env`, salvando nele o conteúdo do arquivo `.env.TEMPLATE`, alterando os valores de acordo com o ambiente de execução. As variáveis nele descritas são as seguintes:

* **URL_LLM**: URL base de onde está sendo executado o LLM. No caso do Ollama, o padrão é `http://localhost:11434`.
* **URL_HOST**: URL onde a aplicação do assistente está sendo executada. É usada na página HTML que serve de interface de usuário, nessa implementação de exemplo. Por padrão, o valor é `http://localhost:8000`, pela Fast API.
* **TIPO_PERSISTENCIA**: define o tipo de armazenamento dos dados de avaliação (valores possíveis, por ora: `'sqlite'` (padrão) e `'mssql'`). A aplicação mantém um registro das interações dos usuários e suas respostas - bem como avaliações dos usuários -, para fins de coleta de dados para eventual refinamento da aplicação. É possível salvar os resultados em um banco SQLite simples, embutido na própria aplicação ou em um banco SQL (MS-SQL, no nosso caso). Para mais detalhes, ver a [seção que descreve o processo de geração do banco](#preparando-o-banco-de-persistência-das-interações).
* **URL_BANCO_SQLITE**: url do eventual arquivo SQLite a ser utilizado como persistência. Por padrão `'api/dados/persistencia.db'`.
* **URL_BANCO_SQL**: URL do eventual banco SQL a ser utilizado como persistência.
* **PORTA_BANCO_SQL**: porta do eventual banco SQL a ser utilizado como persistência.
* **USER_BANCO_SQL**: usuário do eventual banco SQL a ser utilizado como persistência.
* **SENHA_BANCO_SQL**: senha do eventual banco SQL a ser utilizado como persistência.
* **DATABASE_BANCO_SQL**: nome do eventual banco SQL a ser utilizado como persistência.
* **DEVICE**: tipo de dispositivo em que serão realizadas as operações dos modelos de recuperação de documentos no banco de vetores. Se for um processador padrão, utiliza-se `'cpu'` (padrão). Usa-se `'cuda'` nos casos de uma placa de vídeo que utilize a plataforma CUDA. Aplica-se somente à parte da aplicação de recuperação de documentos. O serviço que executa os LLMs (Ollama, no nosso caso), já gerenciam internamente a utilização do dispositivo deisponível.
* **AMBIENTE_EXECUCAO**: Tag a ser utilizada em *logs* de execução (como as ferramentas do Weights and Biases, por exemplo), para identificar qual o dispositivo sendo utilizado. Pode ter qualquer valor, sem quaisquer implicações.

#### Arquivo de Configuração
Igualmente, criar um arquivo de configurações `arq_conf.json`, com conteúdo conforme arquivo `arq_conf_template.json` na pasta `/api/configurações`. Os campos existentes no arquivo de configuração são os seguintes:

* Nomes dos modelos de embeddings possíveis de ser utilizados no Banco de Vetores (valores fixos):
    * **embedding_instructor** (hkunlp/instructor-xl): modelo Instructor da Universidade de Hong Kong
    * **embedding_squad_portuguese** (pierreguillou/bert-base-cased-squad-v1.1-portuguese): Versão em português do BERT
    * **embedding_alibaba_gte** (Alibaba-NLP/gte-multilingual-base): modelo GTE da Alibaba Cloud
    * **embedding_openai** (text-embedding-ada-002): modelo Ada002, da Open AI
    * **embedding_llama** (llama3.1): modelo Llama3.1 da Meta
    * **embedding_deepseek** (deepseek-r1:14b): versão destilada (usando Qwen) do Deepseek R1
    * **embedding_bge_m3** (BAAI/bge-m3): modelo BGE-m3 da Beijing Academy of Artificial Intelligence

* Variáveis de configuração da aplicação
    * **url_indice_documentos**: variável utilizada pela funcionalidade de geração de bancos vetoriais com conteúdo próprio (descrita melhor na [seção que descreve o processo de geração de bancos de vetores](#criando-um-banco-de-vetores-com-conteúdo-customizado))
    * **url_pasta_documentos**: caminho da pasta em que se encontram os documentos base para criação do banco de vetores (descrita melhor na [seção que descreve o processo de geração de bancos de vetores](#criando-um-banco-de-vetores-com-conteúdo-customizado))
    * **url_arquivo_mensagens**: arquivo com o texto base dos prompts a serem enviados ao LLM e as mensagens de retorno ao usuário
    * **threadpool_max_workers**: número máximo de `threads` a serem utilizadas
    * **url_pasta_bancos_vetores**: caminho da pasta em que devem ser armazenados os bancos de vetores criados
    * **url_banco_vetores**: caminho do banco de vetores a ser utilizado na aplicação
    * **nome_colecao_de_documentos**: nome da coleção de documentos a ser utilizada pela aplicação
    * **num_maximo_palavras_por_fragmento**: quantidade máxima de palavras por fragmento de documento a ser incluso em uma coleção (descrito melhor na [seção que descreve o processo de geração de bancos de vetores](#criando-um-banco-de-vetores-com-conteúdo-customizado))
    * **hnsw_space**: métrica utilizada pelo banco vetorial para calcular a similaridade de documentos (`'cosine'` para distância do cosseno).
    * **modelo_funcao_de_embeddings**: nome do modelo escolhido para ser utilizado na função de embeddings
    * **url_cache_modelos**: pasta onde fazer o *cache* dos modelos utilizados
    * **num_documentos_retornados**: quantidade de documentos retornados em uma consulta ao banco vetorial (após testes, verificou-se que, na maioria absoluta dos casos, o documento mais relevante consta entre os 5 documentos com maior similaridade calculada pelo banco de vetores)
    * **url_script_geracao_banco_sqlite**: caminho do script utilizado para gerar o eventual banco de dados SQLite
    * **url_script_geracao_banco_sql**: caminho do script utilizado para gerar o eventual banco SQL
    * **cliente_llm**: nome do cliente LLM a ser utilizado (ex: ollama, openai_api). No momento utilizado somente em *logs* de execução (como as ferramentas do Weights and Biases, por exemplo), para identificar qual o cliente de LLMs está sendo utilizado. Mas eventualmente será importante para os casos em que se quiser escolher outro serviço de geração de texto, como o da Open AI, por exemplo.
    * **modelo_llm**: nome do modelo LLM a ser utilizado na aplicação. Alterando aqui, já é possível utilizar qualquer modelo instalado no Ollama. Necessário impelmentar para outras plataformas
    * **temperature**: temperatura do modelo. Deve ser um float. Valores altos fazem o modelo responder de forma mais criativa
    * **top_k**: valor inteiro que controla a probabilidade de gerar alucinação. Valores altos (ex. 100) resultam em respostas com diversidade; valores baixos (ex. 10) são mais conservadores
    * **top_p**: valor float que atua junto com top_k. Valores altos (ex. 0.95) resultam em texto mais diverso; valores baixos (ex. 0.5) geram texto mais conservador e focado

* Variáveis adicionais
    * **usar_wandb**: durante o desenvolvimento, estamos utilizando a plataforma Weights and Biases para logs e avaliação. Essa variável ativa/desativa o uso da plataforma
    * **wandb_equipe**: nome da equipe em que o projeto foi regitrado no Weights and Biases
    * **wandb_nome_projeto**: nome do projeto no Weights and Biases
    * **wandb_tipo_execucao**: tag para diferenciar as execuções no Weights and Biases
    * **wandb_api_key**: chave de autenticação no Weights and Biases
    * **openai_api_key**: chave da API da Open AI. Utilizada, no momento, somente para uso de embeddings da Open AI nos bancos de vetores.
    * **permitir_comentarios**: habilita o campo de comentários na seção de avaliação na interface de usuário


A ação de criação do arquivo `.env` e do arquivo de configuração pode se executada utilizando os comandos:

```bash
# máquinas Linux
cp api/.env.TEMPLATE api/.env
cp api/configuracoes/arq_conf_template.json api/configuracoes/arq_conf.json
```

```bash
# máquinas Windows
copy api\.env.TEMPLATE api\.env
copy api\configuracoes\arq_conf_template.json api\configuracoes\arq_conf.json
```

## Preparando o banco de vetores

### Banco de Vetores incluso no projeto
Para fins de demonstração e uso direto, neste repositório foram incluídos documentos para geraçaõ do banco vetorial. O conteúdo dos documentos é:

* Regime Jurídico dos Servidores do Rio Grande do Norte
* Regimento Interno da Assembleia Legislativa do Rio Grande do Norte - Alern
* Resolução Nº 089/2017 da Alern
* Resolução Nº 106/2018 da Alern
* Resolução Nº 2388/2019 da Alern
* Resolução Nº 618/2022 da Alern
* Resolução Nº 64/2022 da Alern
* Resolução Nº 77/2024 da Alern
* Resolução Nº 78/2024 da Alern

Para se gerar e utilizar o banco vetorial com os documentos inclusos, utilizando as configurações padrão, executa-se a ferramenta de geração de bancos vetoriais da seguinte forma:

```bash
python -m api.dados.gerenciador_banco_vetores --nome_banco_vetores banco_assistente --lista_colecoes "['documentos_rh_bge_m3']" --lista_nomes_modelos_embeddings "['BAAI/bge-m3']" --comprimento_max_fragmento 300
```

O nome da coleção (`'documentos_rh_bge_m3'`) e o modelo (`BAAI/BGE-m3`) utilizados podem ser alterados, bem como os documentos base a serem usados para geraçaõ do banco vetorial, desde que ajustado o [arquivo de configuração](#arquivo-de-configuração), conforme descrito na sessão abaixo.

### Criando um banco de vetores com conteúdo customizado
Para se criar um banco de vetores, é necessário preparar um conjunto de documentos. Por convenção, são armazenados em `/api/dados/documentos/`. Caso sejam armazenado em outra localização, ajustar o [arquivo de configuração](#arquivo-de-configuração) para `url_pasta_documentos` apontar o caminho correto - bem como `url_indice_documentos`, que normalmente fica junto com os documentos.

Atualmente, há suporte para três formatos de documentos:

* txt - melhor resultado;
* html - bons resultados, mas não tem qualidade perfeita, visto que precisa remover as tags;
* pdf - qualidade altamente dependente da estrutura do documento.

Há suporte para tratamento diferenciado para arquivos com articulação que segue o padrão definido na Lei Complementar no 95/1998. É possível, também, utilizar documentos textuais que tenham sua própria estrutura definida. No caso de PDFs com uma diagramação que impacte o fluxo do texto (muitos quadros, colunas e quebras de texto linear), o resultado pode ser muito pobre.

Os documentos devem ser listados em um arquivo, convencionalmente colocado em `/api/dados/documentos/index.json`, que descreva os dados necessários à extração de seu conteúdo. A estrutura deve ser a seguinte:

* **identificador_do_documento**: uma `string` que sirva para identificar o documento (ex: `lei_acesso_informacao`)
* **url**: caminho em que o arquivo txt/pdf/html se encontra dentro da pasta de documentos
* **titulo**: título do documento
* **autor**: autor do documento
* **fonte**: caminho para um arquivo html
* **texto_articulado**: indicador se o arquivo é dividido em artigos ou não

Um exemplo de como deve ficar:

```json

{   
    "regime_juridico_servidores_rn" : {
        "url": "regime_juridico_servidores_rn.txt",
        "titulo": "Regime Jurídico dos Servidores do Rio Grande do Norte, LEI COMPLEMENTAR ESTADUAL Nº 122, DE 30 DE JUNHO DE 1994",
        "autor": "Governo do Rio Grande do Norte",
        "fonte": "documentos/html/regime_juridico_servidores_rn.html",
        "texto_articulado": true
    },
    (...)
}
```

Pode-se acrescentar mais campos, como `ementa` ou algo semelhante.

Devidamente colocados o `index.json` e os documentos na pasta em questão, é possível utilizar o módulo `api.dados.gerador_banco_vetores` para fazer a geração do banco vetorial.

Para isso, na pasta raiz, basta invocar o módulo, informando os seguintes parâmetros:

* `--nome_banco_vetores`: uma string sem espaço, com o nome do banco vetorial a ser criado
* `--lista_colecoes`: uma string com a lista de nomes das coleções a serem criadas
* `--lista_fn_embeddings`: uma lista dos nomes de modelos de embeddings suportados (ver abaixo) na ordem correspondetes aos nomes das coleções em `--lista_colecoes`
* `--comprimento_max_fragmento`: número máximo de palavras em cada frgmento de arquivo a ser gerado

Os valores por ora aceitos em `--lista_fn_embeddings` são:

*  `"documentos_rh_bge_m3"`: para usar o modelo BGE-m3 da Beijing Academy of Artificial Intelligence
*  `"documentos_rh_openai"`: para usar o modelo Ada002, da Open AI
*  `"documentos_rh_alibaba"`: para usar o modelo GTE da Alibaba Cloud
*  `"documentos_rh_instructor"`: para usar o modelo Instructor da Universidade de Hong Kong
*  `"documentos_rh_bert_pt"`: para usar Versão em português do BERT
*  `"documentos_rh_deepseek"`: para usar a versão destilada (usando Qwen) do Deepseek R1
*  `"documentos_rh_llama"`: para usar o modelo Llama3.1 da Meta

Os testes feitos até o momento apontam o `BAAI/bge-m3` com o a melhor opção.

**OBS:** Não aconselhamos valores acima de 350-400 para `--comprimento_max_fragmento`, visto que utilizamos um modelo (BERT) internamente para realizar reranking dos documentos recuperados.

Exemplos de uso:

```bash
python -m api.dados.gerador_banco_vetores \
--nome_banco_vetores banco_assistente \
--lista_colecoes "['documentos_rh_bge_m3', 'documentos_rh_openai', 'documentos_rh_alibaba', 'documentos_rh_instructor', 'documentos_rh_bert_pt', 'documentos_rh_deepseek', 'documentos_rh_llama']" \
--lista_fn_embeddings "['BAAI/bge-m3', 'text-embedding-ada-002', 'Alibaba-NLP/gte-multilingual-base', 'hkunlp/instructor-xl', 'pierreguillou/bert-base-cased-squad-v1.1-portuguese', 'deepseek-r1:14b', 'llama3.1']" \
--comprimento_max_fragmento 300
```

```bash
python -m api.dados.gerador_banco_vetores \
--nome_banco_vetores banco_assistente \
--lista_colecoes "['documentos_rh_bge_m3']" \
--lista_fn_embeddings "['BAAI/bge-m3']" \
--comprimento_max_fragmento 350
```

Após a criação do banco vetorial, é essencial atualizar o [arquivo de configurações](#arquivo-de-configuração) com a url do banco vetorial (`url_banco_vetores`) e a coleção de documentos (`nome_colecao_de_documentos`) a serem utilizados.

## Preparando o banco de persistência das interações
Todos os dados das interações dos usuários com o assistente são registradas para posterior avaliação/análise, bem como para serem utilizados em algum eventual *finetuning* do modelo LLM. Os dados de interação são registrados em um banco de dados relacional - seja um banco SQL ou um arquivo SQLite, de acordo com o perfil de uso.

Para isso, é necessário incluir no arquivo `/api/.env` a localização do arquivo SQLite ou os dados de conexão do banco SQL (MS-SQL, no nosso caso), conforme [seção que detalha a configuração do `.env`](#arquivo-env), bem como incluir a url do script de geração do banco relacional (`url_script_geracao_banco_sqlite` ou `url_script_geracao_banco_sql`) no arquivo `/api/configuracoes/arq_config.json`, conforme apontado na [seção que descreve o arquivo de configurações](#arquivo-de-configuração).

Após esses ajustes, basta utilizar a aplicação de geração do banco relacional, por meio do módulo `ai.dados.persistencia`:

```python
python -m api.dados.persistencia
```

Feito isso, o projeto está pronto para inicialização.

## Iniciando o projeto
Na pasta raiz do projeto, executar:

```
uvicorn api.api:controller --reload
```
Outras opções possíveis são definir o número de workers, para lidar com concorrência e abrir o host para todas as requisições, em ambiente de desenvolvimento:

```
uvicorn api.api:controller --reload --workers 1 --host 0.0.0.0
```


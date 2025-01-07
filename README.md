# Assistente de Busca
Este repositório é a continuação do projeto RAG-Chat (https://github.com/saintclair-lima/RAG-Chat.git.) Foi reinicializado a partir de uma versão mais estável, após a realizaçaõ de testes.

Para um histórico do processo, clone aquele repositório.

## Ollama: Instalação e Configuração
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

### Adicionando os modelos ao Ollama
No projeto, utilizamos como modelo principal o `Llama3.2`, mas outros modelos são disponíveis para download (como o `phi3.5`, por exemplo).
Para inclusão do modelo, tanto no Windos como no Linux, por meio do terminal/prompt/Powershell, executa-se:

```
ollama pull <nome do modelo>
```
Em nosso caso:
```
ollama pull llama3.2
```
Após a inclusão do modelo no Ollama, pode-se testar se tudo ocorreu corretamente executando o modelo direto no terminal/promt/Powershell:
```
ollama run <nome do modelo>
```
Em nosso caso:
```
ollama run llama3.2
```

### Configurações de Ambiente
De forma a aceitar requisições concorrentes, o Ollama precisa ter alguns parâmetros configurados adequadamente. Para isso, é necessário estabelecer algumas variáveis de ambiente a serem utilizadas por ele, a saber:
* OLLAMA_NUM_PARALLEL
* OLLAMA_MAX_LOADED_MODELS
* OLLAMA_MAX_QUEUE

De acordo com a documentação (ver https://github.com/ollama/ollama/blob/main/docs/faq.md), cada uma das variáveis faz o seguinte:
* `OLLAMA_MAX_LOADED_MODELS` - O número máximo de modelos que podem ser carregados simultaneamente, desde que caibam na memória disponível. O padrão é 3 * o número de GPUs ou 3 para inferência via CPU.
* `OLLAMA_NUM_PARALLEL` - O número máximo de solicitações paralelas que cada modelo processará ao mesmo tempo. O padrão irá selecionar automaticamente 4 ou 1 dependendo da memória disponível.
* `OLLAMA_MAX_QUEUE` - O número máximo de solicitações que Ollama irá enfileirar quando estiver ocupado, antes de rejeitar solicitações adicionais. O padrão é 512.

Outras variáveis de interesse podem ser `OLLAMA_DEBUG` (true para ativar debug) e  `AQUELA_OUTRA_QUE_NAO_CONSIGO_LEMBRAR`.

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

Na pasta raiz do projeto, crie um arquivo `.env`, salvando nele o conteúdo do .env.TEMPLATE, alterando os valores de acordo com o ambiente de execução.

### Instalando as dependências

Dependendo do dispositivo de processamento (CPU/GPU) a ser utilizado, é necessário instalar uma versão específica do `torch`.

Em ambientes que dispõem somente de CPU, nos requirements deve se manter as linhas abaixo:
```
--find-links https://download.pytorch.org/whl/cpu
torch==2.5.0
```

Em ambientes com placa de vídeo com suporte a CUDA, deve-se alterar para buscar a versão adequada to `torch` com o suporte à versão do CUDA que a placa utiliza.

É possível acessar https://pytorch.org/get-started/locally/ e se obter o link adequado, dependendo da versão.

No caso da versão 12.4 do CUDA, é necessaário alterar para:

```
--find-links https://download.pytorch.org/whl/cu124
torch==2.5.0
```

Após esses ajustes, basta instalar os requisitos com:

```
pip install -r requirements.txt
```

Obs: Em alguns casos, há problema de conflito entre a versão do `Numpy` nos requisitos (2.x) e a biblioteca `transformers`. Sendo este o caso, basta instalax uma versão 1.x do `Numpy`.

### Arquivos opcionais inclusos no projeto
Há dois arquivos contidos no projeto que contém dados que podem ser utilizados.
`api/conteudo/bancos_vetores/bancos_vetores.zip` possui um conjunto de bancos vetoriais já prontos para uso -- dentre eles os que foram usados para testes. Cada um deles possui um arquivo `descritor.json` com as configurações utilizadas na sua criação. O que obteve melhores resultados foi a coleção `sem_instrucao` do banco vetorial `resultados_testes` (número máximo de palavras: 300; sem instrução oferecida ao modelo de embeddings).

`api/testes/resultados/testes_automatizados.json.zip` contém os resultados de testes automatizados extensivos feitos sobre o sistema como um todo.

Se for de sua conveniência, a exclusão dos documentos pode ser realizada, dado que são dispensáveis.

### Iniciando o projeto
Na pasta raiz do projeto, executar:
```
uvicorn api.api:app --reload

```



function gerarRespostaFormatada(resposta){
    // AFAZER: Buscar melhores conversores de markdown para html
    var html = `<p>${converterMarkdownHTML(resposta)}</p>\n`
    return html
}

function gerarFontesFormatadas(documentos){
    // Função para limitar o número de palavras exibidas de cada fonte
    const limitarPalavras = (texto, limite = 60) => {
        if (!texto) return '';
        const palavras = texto
            .replace(/<[^>]*>/g, '') // remove tags e marcadores HTML
            .trim()
            .split(/\s+/); // faz quebra por espaço, quebra de linha ou tabulação
        return palavras.slice(0, limite).join(' ') + (palavras.length > limite ? '...' : '');
    };

    var htmlFontes = '';
    if (documentos.length > 0) {
        htmlFontes =                
        `<hr>\n<p class="toggle-fontes-label" id="toggle-fontes-label" onclick="toggleFontes(this)">Mostrar Fontes</p>\n` + 
        `<div class="fontes fontes-fechado" id="fontes">`+
            documentos.map((documento) =>{
                return `
                <div class="documento">
                    <div class="documento-titulo"><a href="${urlHost}/chat/documento?url_documento=${documento.metadados.fonte}" target="_blank">${documento.metadados.titulo} | ${documento.metadados.subtitulo}</a></div>` + 
                    `<div class="documento-conteudo">${limitarPalavras(documento.conteudo)}</div>`+ 
                `</div>`
            }).join("\n") + 
        `</div>`;
    }
    return htmlFontes;
}

function gerarCampoAvaliacaoInteracao(idInteracao){
    htmlAval = `
    <div class="botoes-aval">
        <span class="material-icons icone-aval positivo" onclick="avaliarInteracao(this, '${idInteracao}', 'positivo')">thumb_up<span class="tooltip">Resposta adequada</span></span>
        <span class="material-icons icone-aval negativo" onclick="avaliarInteracao(this, '${idInteracao}', 'negativo')">thumb_down<span class="tooltip">Resposta inadequada</span></span>
        <span class="material-icons icone-aval alerta" onclick="avaliarInteracao(this, '${idInteracao}', 'alerta')">warning<span class="tooltip">Erro grave</span></span>
    </div>`;

    if (mostrarCampoComentario) {
        // AFAZER: Adicionar campo de comentário
        //htmlAval += 
        `<div class="comentario-aval">
            <input type="text">
            <span class="material-icons">comment</span>
        </div>`
    }
    
    return htmlAval
}

function rolagemAutomatica(){
    containerMensagens = document.getElementById("container-exibicao-mensagens");
    const novaMensagem = containerMensagens.lastElementChild;
    const posicaoMargemInferiorContainer = containerMensagens.getBoundingClientRect()['y'] + containerMensagens.getBoundingClientRect()["height"];
    const posicaoMargemInferiorNovaMensagem = novaMensagem.getBoundingClientRect()['y'] + novaMensagem.getBoundingClientRect()["height"];

    // se a margem inferior da mensagem estiver acima da margem inferior do container,
    // faz a rolagem automática
    if (posicaoMargemInferiorNovaMensagem <= (posicaoMargemInferiorContainer + 20)){
        containerMensagens.scrollTop = containerMensagens.scrollHeight;
    }
}

function toggleFontes(elemento) {
    const fontes = elemento.nextElementSibling;
    if (fontes.classList.contains('fontes-fechado')){
        fontes.classList.remove('fontes-fechado');
        fontes.classList.add('fontes-aberto');
        elemento.innerText="Ocultar Fontes"
    } else {
        fontes.classList.remove('fontes-aberto');
        fontes.classList.add('fontes-fechado');
        elemento.innerText="Mostrar Fontes"
    }
}

function processarJSON(texto){
    const resultados = [];
    let parcial;
    let linhas = texto.split('\n')
    for (let linha of linhas){
        // se a linha não for vazia
        if(linha !== ''){
            try {
                //converte em JSON
                parcial = JSON.parse(linha.trim());
            } catch (erro) {
                if (erro instanceof SyntaxError) {
                    // Indica que o JSON está incompleto. Mantém para concatenar com
                    // o restante, para criar o JSON posterior.
                    parcial = linha;
                } else {
                    throw erro;
                }
            }
            resultados.push(parcial);
        }
    }
    return resultados;
}

async function enviarPergunta(){
    // Só executa se houver valor digitado no campo de pergunta
    if (document.getElementById("text-input").value){
        document.getElementById("botao-enviar").disabled = true;
        document.getElementById("text-input").disabled = true;
        var pergunta = document.getElementById("text-input").value;
        document.getElementById("text-input").value = "";
        var divPergunta = document.createElement("div");
        divPergunta.className = "text-box";
        divPergunta.textContent = pergunta;
        divPergunta.classList.add("align-right");
        divPergunta.classList.add("mensagem-enviada");
        document.getElementById("container-exibicao-mensagens").appendChild(divPergunta);

        
        var divResposta = document.createElement("div");
        divResposta.className = "text-box";
        divResposta.innerHTML = "<i>Pensando sobre a pergunta</i> <span class='dots'><span class='dot1'>.</span><span class='dot2'>.</span><span class='dot3'>.</span></span>";
        divResposta.classList.add("align-left");
        divResposta.classList.add("mensagem-recebida");
        document.getElementById("container-exibicao-mensagens").appendChild(divResposta);
        // rola a página até o início da nova mensagem
        document.getElementById("container-exibicao-mensagens").scrollTop = document.getElementById("container-exibicao-mensagens").scrollHeight;


        let habilitarCampos = false;

        const controller = new AbortController();
        //AFAZER: Ajustar Timeout. levar em consideração demora do Ollama em responder
        const timeoutId = setTimeout(() => controller.abort(), 120000);

        
        let respostaLLM = "";
        let documentos = [];

        try {
            const response = await fetch(`${urlHost}/chat/enviar-pergunta/`, {
                method: "POST",
                body: JSON.stringify({
                    pergunta: pergunta,
                    historico: historico,
                    id_sessao: idSessao,
                    id_cliente: idCliente,
                    intencao: null
                }),
                headers: {
                    "Content-type": "application/json; charset=UTF-8"
                },
                // Passa o sinal de cancelamento
                signal: controller.signal
            });
            
            // Limpa o timeout se a resposta for recebida a tempo
            clearTimeout(timeoutId);

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");

            let valoresDecodificados = "";
            while (true) {
                rolagemAutomatica();
                const { done, value } = await reader.read();
                if (done) break;
                valoresDecodificados += decoder.decode(value);

                let listaConteudoJSON = processarJSON(valoresDecodificados);
                let fragmentoJSONIncompleto;
                for (let conteudoJSON of listaConteudoJSON){
                    fragmentoJSONIncompleto = '';
                    if (conteudoJSON.tipo == 'erro') {
                        console.error(`${conteudoJSON.descricao}: ${conteudoJSON.mensagem}`);
                        divResposta.classList.remove("mensagem-recebida");
                        divResposta.classList.add("mensagem-erro");
                        divResposta.innerHTML = conteudoJSON.mensagem;
                        habilitarCampos = true;
                        break;
                    } else if (conteudoJSON.tipo == 'info') {
                        console.info(`${conteudoJSON.descricao}: ${conteudoJSON.mensagem? conteudoJSON.mensagem : '<sem conteúdo>'}`);
                        continue;
                    } else if (conteudoJSON.tipo == 'controle') {
                        if (conteudoJSON.dados.tag == 'status') {
                            divResposta.innerHTML = `<i>${conteudoJSON.dados.conteudo}</i> <span class='dots'><span class='dot1'>.</span><span class='dot2'>.</span><span class='dot3'>.</span></span>`;
                        }
                        continue;
                    } else if (conteudoJSON.tipo == 'dados') {
                        if (conteudoJSON.dados.tag == 'frag-resposta-llm') {
                            respostaLLM += conteudoJSON.dados.conteudo;
                            divResposta.innerHTML = gerarRespostaFormatada(respostaLLM);
                        } else if (conteudoJSON.dados.tag == 'lista-docs-recuperados') {
                            documentos = conteudoJSON.dados.conteudo;
                        } else if (conteudoJSON.dados.tag == 'interacao-finalizada') {
                            if (respostaLLM) divResposta.innerHTML = gerarRespostaFormatada(respostaLLM) + gerarFontesFormatadas(documentos) + gerarCampoAvaliacaoInteracao(conteudoJSON.dados.conteudo);
                            else divResposta.innerHTML = divResposta.innerHTML + gerarCampoAvaliacaoInteracao(conteudoJSON.dados.conteudo);
                            
                            // mantém o histórico com no máximo 5 mensagens na memória
                            if (historico.length == 5) historico.shift();
                            historico.push([pergunta, respostaLLM]);
                            habilitarCampos = true;
                        } else if (conteudoJSON.dados.tag == 'servir-documento') {
                            divResposta.innerHTML = conteudoJSON.dados.conteudo;
                        }
                        continue;
                    } else if (typeof conteudoJSON === 'string') {
                        // A função processarJSON devolve em formato de string os conteúdos que não podem ser convertidos em objetos.
                        // Depreende-se disso que se trata de um fragmento incompleto de um JSON.
                        // Então guarda para concatenar com o conteúdo que vai ser recebido, com a parte restante do JSON
                        fragmentoJSONIncompleto = conteudoJSON;
                        continue;
                    } else {
                        console.info(conteudoJSON);
                        continue;
                    }
                }

                // Limpa o 'buffer' para receber novo conteúdo. Não executa caso hava um fragmento de JSON incompleto
                valoresDecodificados = '' + fragmentoJSONIncompleto;
            }
        } catch (erro) {
            // Garante reset do timeout
            clearTimeout(timeoutId);
            console.error("Erro:", erro);

            divResposta.classList.remove("mensagem-recebida");
            divResposta.classList.add("mensagem-erro");
            let msg_erro = ''
            if (erro.name === "AbortError") {
                msg_erro = "O servidor demorou para responder. Tente novamente mais tarde.";
            } else {
                msg_erro = "Ocorreu um erro na comunicação com o servidor.";
                console.error(`${msg_erro} (Tipo do erro: ${erro.name})`);
            }

            if (respostaLLM != '') msg_erro = gerarRespostaFormatada(respostaLLM) + `\n<hr><p>${msg_erro}</p>`

            divResposta.innerHTML = msg_erro
            habilitarCampos=true;
        }
        if (habilitarCampos){
            document.getElementById("botao-enviar").removeAttribute("disabled");
            document.getElementById("text-input").removeAttribute("disabled");
            document.getElementById("text-input").focus();
        }
    }
}

async function avaliarInteracao(elementoClicado, idInteracao, avaliacao){
    // Alterar quando implementada a lógica de incluir comentário
    let comentario = null;

    // Se o elemento está clicado/avaliado, setar para null para remover avaliação
    if (elementoClicado.classList.contains('clicado')) avaliacao = null;

    const containerBotoesAval = elementoClicado.parentElement;

    fetch(`${urlHost}/chat/avaliar-interacao/`, {
        method: "POST",
        body: JSON.stringify({
            uuid_interacao: idInteracao,
            avaliacao: avaliacao,
            comentario: comentario
        }),
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        },
    })
    .then(response => {
        if (!response.ok) throw new Error('A resposta do servidor aponta que houve um problema');
        
        return response.json();
    })
    .then(data => {
        data = JSON.parse(data);
        const sucessoAvaliacao = data.dados.conteudo.sucesso_avaliacao;
        const mensagemRetorno = data.dados.conteudo.mensagem_retorno;
        
        if (! elementoClicado.classList.contains('clicado') && sucessoAvaliacao) {
            if (elementoClicado.classList.contains('positivo')) {
                elementoClicado.classList.remove('cinza');
                elementoClicado.classList.add('verde');
            }
            if (elementoClicado.classList.contains('negativo')) {
                elementoClicado.classList.remove('cinza');
                elementoClicado.classList.add('laranja');
            }
            if (elementoClicado.classList.contains('alerta')) {
                elementoClicado.classList.remove('cinza');
                elementoClicado.classList.add('vermelho');
            }
    
            elementoClicado.classList.add('clicado');    
            Array.from(containerBotoesAval.children).forEach(child => {
                if (child !== elementoClicado) {
                    child.classList.remove('verde');
                    child.classList.remove('vermelho');
                    child.classList.remove('laranja');
                    child.classList.add('cinza');
                    child.style.display = 'none';
                }
            });
        } else if (elementoClicado.classList.contains('clicado') && sucessoAvaliacao){
            elementoClicado.classList.remove('clicado');
            Array.from(containerBotoesAval.children).forEach(child => {
                child.classList.remove('verde');
                child.classList.remove('vermelho');
                child.classList.remove('laranja');
                child.classList.add('cinza');
                child.style.display = 'inline-block';
            }); 
        } else if(! resultado.sucessso_avaliacao){
            alert(mensagemRetorno);
        }
    })
    .catch((error) => {
        if (error instanceof TypeError) {
            console.error('Falha no fetch devido a problemas de rede ou com a URL:', error);
            alert('Erro ao enviar avaliação. Verifique sua conexão.');
        } else {
            console.error('Um erro inesperado ocorreu no envio da avaliação:', error);
        }
    });
}

function salvarConversa() {
    var cabecalho = document.getElementsByClassName('cabecalho')[0].cloneNode(true);
    var labelSessao = document.createElement('div');
    labelSessao.classList.add('identificador-sessao');
    labelSessao.innerHTML = (`<strong>ID da Sessão:</strong> ${idSessao}`)
    var mensagens = Array.from(document.getElementsByClassName('text-box'));
    // Remove mensagem inicial do Assistente
    mensagens.shift();
    var wrapper = document.createElement('div');
    wrapper.classList.add('pdf-wrapper');
    wrapper.appendChild(cabecalho);
    wrapper.appendChild(labelSessao);
    mensagens.forEach(msg => {
        // Clona o elemento para não interferir nos elementos exibidos em tela
        var clone = msg.cloneNode(true);
        wrapper.appendChild(clone);
    });    
    document.body.appendChild(wrapper);
    document.body.style.backgroundColor = "white";
    window.print();
    document.body.removeChild(wrapper);
    document.body.style.backgroundColor = "#f6f6f6";
}
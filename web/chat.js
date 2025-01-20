

function gerarRespostaFormatada(resposta){
    var html = `<p>${converterMarkdownHTML(resposta)}</p>\n`
    return html
}

function gerarFontesFormatadas(documentos){
    var htmlFontes =                
        `<hr>\n<p class="toggle-fontes-label" id="toggle-fontes-label" onclick="toggleFontes(this)">Mostrar Fontes</p>\n` + 
        `<div class="fontes fontes-fechado" id="fontes">`+
            documentos.map((documento) =>{
                return `
                <div class="documento">
                    <div class="documento-titulo"><a href="${documento.metadados.fonte}" target="_blank">${documento.metadados.titulo} | ${documento.metadados.subtitulo}</a></div>` + 
                    `<div class="documento-conteudo">${documento.conteudo}</div>`+ 
                `</div>`
            }).join("\n") + 
        `</div>`;
    
    return htmlFontes;
}

function gerarCampoAvaliacaoInteracao(idInteracao){
    console.log(idInteracao);
    htmlAval = `
    <div class="area-aval">
        <span id="posit_aval" class="material-icons icone-aval positivo" onclick="avaliarInteracao(this, '${idInteracao}', 'positivo')">thumb_up</span>
        <span id="negat_aval" class="material-icons icone-aval negativo" onclick="avaliarInteracao(this, '${idInteracao}', 'negativo')">thumb_down</span>
        <span id="alert_aval" class="material-icons icone-aval alerta" onclick="avaliarInteracao(this, '${idInteracao}', 'alerta')">warning</span>
    </div>`;
    
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
        divResposta.innerHTML = "<span class='dots'><span class='dot1'>.</span><span class='dot2'>.</span><span class='dot3'>.</span></span>";
        divResposta.classList.add("align-left");
        divResposta.classList.add("mensagem-recebida");
        document.getElementById("container-exibicao-mensagens").appendChild(divResposta);
        // rola a página até o início da nova mensagem
        document.getElementById("container-exibicao-mensagens").scrollTop = document.getElementById("container-exibicao-mensagens").scrollHeight;


        let habilitarCampos = false;

        const controller = new AbortController();
        //AFAZER: Ajustar Timeout. levar em consideração demora do Ollama em responder
        const timeoutId = setTimeout(() => controller.abort(), 120000);

        try {
            const response = await fetch(`${url_host}/chat/enviar-pergunta/`, {
                method: "POST",
                body: JSON.stringify({
                    pergunta: pergunta,
                    historico: historico,
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
            let respostaLLM = "";
            let documentos = [];

            while (true) {
                rolagemAutomatica();
                const { done, value } = await reader.read();
                if (done) break;
                valores_decodificados = decoder.decode(value)

                for (let linha of valores_decodificados.split('\n')){
                    if (linha.trim() === '') continue;
                    try {
                        var retorno = JSON.parse(linha.trim());
                        if (retorno.tipo == 'erro') {
                            console.error(`${retorno.descricao}: ${retorno.mensagem}`);
                            divResposta.classList.remove("mensagem-recebida");
                            divResposta.classList.add("mensagem-erro");
                            divResposta.innerHTML = retorno.mensagem;
                            habilitarCampos = true;
                            break;
                        } else if (retorno.tipo == 'info') {
                            console.info(`${retorno.descricao}: ${retorno.mensagem? retorno.mensagem : '<sem conteúdo>'}`);
                            continue;
                        } else if (retorno.tipo == 'controle') {
                            if (retorno.dados.tag == 'status') {
                                divResposta.innerHTML = `<i>${retorno.dados.conteudo}<i> <span class='dots'><span class='dot1'>.</span><span class='dot2'>.</span><span class='dot3'>.</span></span>`;
                            }
                            continue;
                        } else if (retorno.tipo == 'dados') {
                            if (retorno.dados.tag == 'frag-resposta-llm') {
                                respostaLLM += retorno.dados.conteudo;
                                divResposta.innerHTML = gerarRespostaFormatada(respostaLLM);
                            } else if (retorno.dados.tag == 'lista-docs-recuperados') {
                                documentos = retorno.dados.conteudo;
                            } else if (retorno.dados.tag == 'persistencia-interacao') {
                                divResposta.innerHTML = gerarRespostaFormatada(respostaLLM) + gerarFontesFormatadas(documentos) + gerarCampoAvaliacaoInteracao(retorno.dados.conteudo);
                                historico.push([pergunta, respostaLLM])
                                habilitarCampos = true;
                            }
                            continue;
                        } else {
                            console.info(retorno);
                            continue;
                        }
                    } catch (erro) {
                        console.error(erro);
                        console.info(linha);
                        habilitarCampos = true;
                        break;
                    }
                }
            }
        } catch (erro) {
            // Garante reset do timeout
            clearTimeout(timeoutId);
            console.error("Erro:", erro);

            divResposta.classList.remove("mensagem-recebida");
            divResposta.classList.add("mensagem-erro");
            // AFAZER: Verificar essas mensagens
            if (erro.name === "AbortError") {
                divResposta.innerHTML = "O servidor demorou para responder. Tente novamente mais tarde.";
            } else {
                divResposta.innerHTML = `Ocorreu um erro ao tentar se conectar ao servidor. (Tipo do erro: ${erro.name})`;
            }
            habilitarCampos=true;
        }
        if (habilitarCampos){
            document.getElementById("botao-enviar").removeAttribute("disabled");
            document.getElementById("text-input").removeAttribute("disabled");
            document.getElementById("text-input").focus();
        }
    }
}

async function enviarAvaliacao(idInteracao, avaliacao, comentario) {
    fetch(`${url_host}/chat/avaliar-interacao/`, {
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
        if (!response.ok) {
            throw new Error(`Erro HTTP! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(result => {
        if (result.success) {
            console.log("Avaliação enviada com sucesso:", result.data);
        } else {
            console.warn("Algo deu errado:", result.message);
        }
    })
    .catch(error => {
        console.error("Falha no envio da avaliacao:", error.message);
    });
}

async function avaliarInteracao(elementoClicado, idInteracao, avaliacao){
    const parent = elementoClicado.parentElement;

    if (! elementoClicado.classList.contains('clicado')) {

        enviarAvaliacao(idInteracao, avaliacao, null);

        if (elementoClicado.classList.contains('positivo'))
            elementoClicado.style.color = 'green';
        if (elementoClicado.classList.contains('negativo'))
            elementoClicado.style.color = 'orange';
        if (elementoClicado.classList.contains('alerta'))
            elementoClicado.style.color = 'red';

        elementoClicado.classList.add('clicado');  
    
        Array.from(parent.children).forEach(child => {
            if (child !== elementoClicado) {
                child.style.color = 'gray';
                child.style.display = 'none';
            }
        });
    } else {

        enviarAvaliacao(idInteracao, null, null);

        elementoClicado.classList.remove('clicado');
        Array.from(parent.children).forEach(child => {
            child.style.color = 'gray';
            child.style.display = 'inline-block';
        }); 
    }
}

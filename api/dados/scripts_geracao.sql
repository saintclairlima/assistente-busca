CREATE TABLE Colecao (
    Id_Colecao INT NOT NULL,
    Nome VARCHAR(500),
    Banco_Vetores VARCHAR(500),
    Nome_Modelo_Fn_Embeddings VARCHAR(500),
    Tipo_Modelo_Fn_Embeddings VARCHAR(500),
    Instrucao VARCHAR(MAX),
    Qtd_Max_Palavras INT,
    CONSTRAINT Pk_Colecao PRIMARY KEY (Id_Colecao));

CREATE TABLE Documento (
    Id_Documento INT NOT NULL,
    Tag_Id_Metadados VARCHAR(500),
    Conteudo VARCHAR(MAX),
    Titulo VARCHAR(500),
    Subtitulo VARCHAR(2000),
    Autor VARCHAR(2000),
    Fonte VARCHAR(2000),
    Id_Colecao INT,
    CONSTRAINT Pk_Documento PRIMARY KEY (Id_Documento));

CREATE TABLE Interacao (
    Id_Interacao INT NOT NULL,
    Pergunta VARCHAR(MAX),
    Tipo_Dispositivo_Aplicacao VARCHAR(500),
    Tipo_Dispositivo_LLM VARCHAR(500),
    LLM_Nome_Modelo VARCHAR(500),
    LLM_Tempo_Total NUMERIC,
    LLM_Tempo_Carregamento NUMERIC,
    LLM_Num_Tokens_Prompt INT,
    LLM_Tempo_Processamento_Prompt NUMERIC,
    LLM_Num_Tokens_Resposta INT,
    LLM_Tempo_Processamento_Resposta NUMERIC,
    LLM_Historico VARCHAR(MAX),
    LLM_Resposta VARCHAR(MAX),
    LLM_Tempo_Inicio_Stream NUMERIC, 
    Tempo_Recuperacao_Documentos NUMERIC,
    Tempo_Avaliacao_Bert NUMERIC,
    CONSTRAINT Pk_Interacao PRIMARY KEY (Id_Interacao)
);

CREATE TABLE Documento_em_Interacao (
    Resposta_Bert VARCHAR(MAX), 
    Score_Bert NUMERIC,
    Score_Distancia NUMERIC,
    Score_Ponderado NUMERIC,
    Id_Documento INT,
    Id_Interacao INT,
    CONSTRAINT Pk_Documento_em_Interacao PRIMARY KEY (Id_Documento, Id_Interacao));

ALTER TABLE Documento ADD CONSTRAINT Fk_Documento_Colecao FOREIGN KEY(Id_Colecao) REFERENCES Colecao (Id_Colecao);
ALTER TABLE Documento_em_Interacao ADD CONSTRAINT Fk_Documento_em_Interacao_Documento FOREIGN KEY(Id_Documento) REFERENCES Documento (Id_Documento);
ALTER TABLE Documento_em_Interacao ADD CONSTRAINT Fk_Documento_em_Interacao_Interacao FOREIGN KEY(Id_Interacao) REFERENCES Interacao (Id_Interacao);
CREATE TABLE Colecao (
    UUID_Colecao UNIQUEIDENTIFIER NOT NULL,
    Nome VARCHAR(500),
    Banco_Vetores VARCHAR(500),
    Nome_Modelo_Fn_Embeddings VARCHAR(500),
    Tipo_Modelo_Fn_Embeddings VARCHAR(500),
    Instrucao VARCHAR(MAX),
    Qtd_Max_Palavras INT,
    Metrica_Similaridade VARCHAR(50),
    Data_Criacao DATETIME DEFAULT GETDATE(),
    CONSTRAINT Pk_Colecao PRIMARY KEY (UUID_Colecao));

CREATE TABLE Documento (
    UUID_Documento UNIQUEIDENTIFIER NOT NULL,
    Tag_Fragmento VARCHAR(500),
    Conteudo VARCHAR(MAX),
    Titulo VARCHAR(500),
    Subtitulo VARCHAR(2000),
    Autor VARCHAR(2000),
    Fonte VARCHAR(2000),
    UUID_Colecao UNIQUEIDENTIFIER,
    Data_Criacao DATETIME DEFAULT GETDATE(),
    CONSTRAINT Pk_Documento PRIMARY KEY (UUID_Documento));

CREATE TABLE Interacao (
    UUID_Interacao UNIQUEIDENTIFIER NOT NULL,
    Pergunta VARCHAR(MAX),
    Tipo_Dispositivo_Aplicacao VARCHAR(500),
    Tipo_Dispositivo_LLM VARCHAR(500),
    Tempo_Recuperacao_Documentos NUMERIC,
    Tempo_Estimativa_Bert NUMERIC,
    LLM_Template_System VARCHAR(MAX),
    LLM_Historico VARCHAR(MAX),
    LLM_Cliente VARCHAR(500),
    LLM_Nome_Modelo VARCHAR(500),
    LLM_Tempo_Carregamento NUMERIC,
    LLM_Num_Tokens_Prompt INT,
    LLM_Tempo_Processamento_Prompt NUMERIC,
    LLM_Num_Tokens_Resposta INT,
    LLM_Tempo_Processamento_Resposta NUMERIC,
    LLM_Tempo_Inicio_Stream NUMERIC, 
    LLM_Tempo_Total NUMERIC,
    LLM_Resposta VARCHAR(MAX),
    LLM_Tipo_Conclusao VARCHAR(50),
    JSON_Interacao VARCHAR(MAX),
    UUID_Sessao UNIQUEIDENTIFIER,
    Data_Criacao DATETIME DEFAULT GETDATE(),
    CONSTRAINT Pk_Interacao PRIMARY KEY (UUID_Interacao));

CREATE TABLE Documento_em_Interacao (
    UUID_Documento UNIQUEIDENTIFIER NOT NULL,
    UUID_Interacao UNIQUEIDENTIFIER NOT NULL,
    Resposta_Bert VARCHAR(MAX), 
    Score_Bert NUMERIC,
    Score_Distancia NUMERIC,
    Score_Ponderado NUMERIC,
    Data_Criacao DATETIME DEFAULT GETDATE(),
    CONSTRAINT Pk_Documento_em_Interacao PRIMARY KEY (UUID_Documento, UUID_Interacao));

CREATE TABLE Avaliacao_Interacao (
    UUID_Interacao UNIQUEIDENTIFIER NOT NULL,
    Avaliacao VARCHAR(40),
    Comentario VARCHAR(MAX),
    Data_Criacao DATETIME DEFAULT GETDATE(),
    CONSTRAINT Pk_Avaliacao_Interacao PRIMARY KEY (UUID_Interacao));

ALTER TABLE Documento ADD CONSTRAINT Fk_Documento_Colecao FOREIGN KEY(UUID_Colecao) REFERENCES Colecao (UUID_Colecao);
ALTER TABLE Documento_em_Interacao ADD CONSTRAINT Fk_Documento_em_Interacao_Documento FOREIGN KEY(UUID_Documento) REFERENCES Documento (UUID_Documento);
ALTER TABLE Documento_em_Interacao ADD CONSTRAINT Fk_Documento_em_Interacao_Interacao FOREIGN KEY(UUID_Interacao) REFERENCES Interacao (UUID_Interacao);
ALTER TABLE Avaliacao_Interacao ADD CONSTRAINT Fk_Avaliacao_Interacao FOREIGN KEY (UUID_Interacao) REFERENCES Interacao (UUID_Interacao);
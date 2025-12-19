CREATE TABLE Colecao (
    UUID_Colecao TEXT NOT NULL,
    Nome TEXT,
    Banco_Vetores TEXT,
    Nome_Modelo_Fn_Embeddings TEXT,
    Tipo_Modelo_Fn_Embeddings TEXT,
    Instrucao TEXT,
    Qtd_Max_Palavras INTEGER,
    Metrica_Similaridade TEXT,
    Data_Criacao DATETIME DEFAULT (CURRENT_TIMESTAMP),
    PRIMARY KEY (UUID_Colecao)
);

CREATE TABLE Documento (
    UUID_Documento TEXT NOT NULL,
    Tag_Fragmento TEXT,
    Conteudo TEXT,
    Titulo TEXT,
    Subtitulo TEXT,
    Autor TEXT,
    Fonte TEXT,
    UUID_Colecao TEXT,
    Data_Criacao DATETIME DEFAULT (CURRENT_TIMESTAMP),
    PRIMARY KEY (UUID_Documento),
    FOREIGN KEY (UUID_Colecao) REFERENCES Colecao (UUID_Colecao)
);

CREATE TABLE Interacao (
    UUID_Interacao TEXT NOT NULL,
    Pergunta TEXT,
    Tipo_Dispositivo_Aplicacao TEXT,
    Tipo_Dispositivo_LLM TEXT,
    Tempo_Recuperacao_Documentos REAL,
    Tempo_Estimativa_Bert REAL,
    LLM_Template_System TEXT,
    LLM_Historico TEXT,
    LLM_Cliente TEXT,
    LLM_Nome_Modelo TEXT,
    LLM_Tempo_Carregamento REAL,
    LLM_Num_Tokens_Prompt INTEGER,
    LLM_Tempo_Processamento_Prompt REAL,
    LLM_Num_Tokens_Resposta INTEGER,
    LLM_Tempo_Processamento_Resposta REAL,
    LLM_Tempo_Inicio_Stream REAL, 
    LLM_Tempo_Total REAL,
    LLM_Resposta TEXT,
    LLM_Tipo_Conclusao TEXT,
    Intencao TEXT,
    JSON_Interacao TEXT,
    UUID_Sessao TEXT,
    UUID_Cliente TEXT,
    Data_Criacao DATETIME DEFAULT (CURRENT_TIMESTAMP),
    PRIMARY KEY (UUID_Interacao)
);

CREATE TABLE Documento_em_Interacao (
    UUID_Documento TEXT NOT NULL,
    UUID_Interacao TEXT NOT NULL,
    Resposta_Bert TEXT, 
    Score_Bert REAL,
    Score_Distancia REAL,
    Score_Ponderado REAL,
    Data_Criacao DATETIME DEFAULT (CURRENT_TIMESTAMP),
    PRIMARY KEY (UUID_Documento, UUID_Interacao),
    FOREIGN KEY (UUID_Documento) REFERENCES Documento (UUID_Documento),
    FOREIGN KEY (UUID_Interacao) REFERENCES Interacao (UUID_Interacao)
);

CREATE TABLE Avaliacao_Interacao (
    UUID_Interacao TEXT NOT NULL,
    Avaliacao TEXT, 
    Comentario TEXT,
    Data_Criacao DATETIME DEFAULT (CURRENT_TIMESTAMP),
    PRIMARY KEY (UUID_Interacao),
    FOREIGN KEY (UUID_Interacao) REFERENCES Interacao (UUID_Interacao)
);
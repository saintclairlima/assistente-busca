print('Carregando classificador de intenção...')
import os
import joblib
import csv
import json

from datetime import datetime
from typing import Dict, List
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sentence_transformers import SentenceTransformer
from torch import cuda

from api.configuracoes.config_gerais import configuracoes

class ClassificadorIntencao:
    def treinar_modelo(self, caminho_dados:str, caminho_classificador:str, pipeline=None, log_progresso:bool=False, aplica_testes:bool=True) -> None:
        raise NotImplementedError('Método treinar_modelo() não foi implantado para esta classe')
    
    def carregar_modelo(self, caminho_classificador:str) -> None:
        raise NotImplementedError('Método carregar_modelo() não foi implantado para esta classe')

    def classificar_intencao(self, texto:str) -> str:
        raise NotImplementedError('Método classificar_intencao() não foi implantado para esta classe')

    def classificar_intencao_proba(self, texto:str) -> Dict[str, float]:
        raise NotImplementedError('Método classificar_intencao_proba() não foi implantado para esta classe')

    def classificar_intencoes(self, textos:List[str]) -> List[str]:
        raise NotImplementedError('Método classificar_intencoes() não foi implantado para esta classe')
    
    def classificar_intencoes_proba(self, textos:List[str]) -> List[ Dict[str, float]]:
        raise NotImplementedError('Método classificar_intencoes_proba() não foi implantado para esta classe')
    
    def descrever(self):
        print(json.dumps(self.metadados, indent=2))

class ClassificadorIntencaoTfidf(ClassificadorIntencao):
    def __init__(
        self,
        caminho_dados='api/dados/classificador_de_intencao/dataset-treinamento-intencao-dialogar.csv',
        caminho_classificador='api/modelos/classificador_intencao_tfidf.joblib',
        pipeline=None,
        log_progresso=False
    ):
        self.metadados = {
            "data_criacao": datetime.now().isoformat(),
            "dados_treinamento": caminho_dados,
            "representacao_dados": {
                "tipo": "tfidf"
            },
        }

        # Tenta carregar, senão treina
        if os.path.exists(caminho_classificador):
            self.carregar_modelo(caminho_classificador)
        else:
            self.treinar_modelo(
                caminho_dados=caminho_dados,
                caminho_classificador=caminho_classificador,
                pipeline=pipeline,
                log_progresso=log_progresso)

    def treinar_modelo(self, caminho_dados:str, caminho_classificador:str, pipeline=None, log_progresso:bool=False, aplica_testes:bool=True) -> None:
        print('-- Preparando recursos...')
        from sklearn.pipeline import Pipeline
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import RidgeClassifier
        import joblib
        import nltk
        from nltk.corpus import stopwords
        nltk.download('stopwords')
        stopwords_pt = stopwords.words('portuguese')

        print('-- Lendo dados de treinamento...')
        with open(caminho_dados, 'r', encoding='utf-8') as arq:
            reader = csv.reader(arq)
            dados = [row for row in reader]
        
        X = [item[1] for item in dados[1:]]
        y = [item[2] for item in dados[1:]]
        print(f'--- aquivo com {len(X)} instâncias')
        print(f'--- rótulos das instâncias:')
        print(f"""{'\n'.join([f"    {item}\t{y.count(item)}" for item in set(y)])}""")

        print('-- Treinando classificador Tfidf...')
        if not pipeline:
            pipeline = Pipeline([
                ("tfidf", TfidfVectorizer(
                    stop_words=stopwords_pt,
                    max_df=0.5492819135282642,
                    min_df=1,
                    ngram_range=(1, 1),
                    max_features=11500,
                    use_idf=True,
                    sublinear_tf=False,
                    norm='l2'
                )),
                ("classificador", RidgeClassifier(
                    alpha=1.0,
                    class_weight=None,
                    copy_X=True,
                    fit_intercept=True,
                    max_iter=None,
                    positive=False,
                    random_state=42,
                    solver='auto',
                    tol=0.0001
                ))
            ])

        # Fit the pipeline on the training data
        if aplica_testes:
            from sklearn.metrics import classification_report
            from sklearn.model_selection import cross_val_predict, StratifiedKFold

            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            y_pred = cross_val_predict(pipeline, X, y, cv=cv, verbose=1)
            metricas_treinamento = classification_report(y, y_pred, output_dict=True)
        
        pipeline.fit(X, y)
        
        self.metadados.update({
            'classes': [str(classe) for classe in pipeline.named_steps['classificador'].classes_],
            "classificador": str(pipeline),
            'metricas_treinamento': metricas_treinamento
        })

        print(f'-- Salvando classificador ({caminho_classificador})')
        joblib.dump(pipeline, caminho_classificador)
        with open(f'{caminho_classificador.replace('.joblib', '_descritor.json')}', 'w', encoding='utf-8') as arq:
            json.dump(self.metadados, arq, ensure_ascii=False, indent=2)

        self.classificador = pipeline
        print('-- Classificador salvo sucesso!')


    def carregar_modelo(self, caminho_classificador:str) -> None:
        print(f'-- Carregando classificador salvo ({caminho_classificador})')
        self.classificador = joblib.load(caminho_classificador)

        with open(caminho_classificador.replace('.joblib', '_descritor.json')) as arq:
            self.metadados = json.load(arq)

        print(f'--- classificador treinado com os rótulos: {', '.join(self.classificador.classes_)}')

    def classificar_intencao(self, texto:str) -> str:
        embeddings = self.embedder.encode([texto])
        return str(self.classificador.predict(embeddings)[0])
    
    def classificar_intencao_proba(self, texto:str) -> Dict[str, float]:
        embeddings = self.embedder.encode([texto])
        probabilidades = self.classificador.predict_proba(embeddings)[0]
        classes = self.classificador.classes_
        return {str(classe): float(probabilidade) for classe, probabilidade in zip(classes, probabilidades)}

    
    def classificar_intencoes(self, textos:List[str]) -> List[str]:
        embeddings = self.embedder.encode(textos)
        return [str(classe) for classe in self.classificador.predict(embeddings)]
    
    def classificar_intencoes_proba(self, textos:List[str]) -> List[ Dict[str, float]]:
        embeddings = self.embedder.encode(textos)
        resultados =  self.classificador.predict_proba(embeddings)
        classes = self.classificador.classes_

        return [
            {str(classe): float(probabilidade) for classe, probabilidade in zip(classes, probabilidades)}
            for probabilidades in resultados
        ]


class ClassificadorIntencaoEmbeddings(ClassificadorIntencao):
    def __init__(
        self,
        caminho_dados='api/dados/classificador_de_intencao/dataset-treinamento-intencao-dialogar.csv',
        caminho_classificador='api/modelos/classificador_intencao_embeddings.joblib',
        modelo_embeddings=configuracoes.embedding_bge_m3,
        pipeline=None,
        log_progresso=False
    ):
        
        device = 'cuda' if cuda.is_available() else 'cpu'
        print(f'-- Carregando modelo de embeddings ({modelo_embeddings})')
        self.embedder = SentenceTransformer(modelo_embeddings, device=device, trust_remote_code=True)

        self.metadados = {
            "data_criacao": datetime.now().isoformat(),
            "dados_treinamento": caminho_dados,
            "representacao_dados": {
                "tipo": "text_embeddings",
                "modelo": modelo_embeddings
            },
        }

        # Tenta carregar, senão treina
        if os.path.exists(caminho_classificador):
            self.carregar_modelo(caminho_classificador)
        else:
            self.treinar_modelo(
                caminho_dados=caminho_dados,
                caminho_classificador=caminho_classificador,
                pipeline=pipeline,
                log_progresso=log_progresso)

    def treinar_modelo(self, caminho_dados:str, caminho_classificador:str, pipeline=None, log_progresso:bool=False, aplica_testes:bool=True) -> None:
        print('-- Lendo dados de treinamento...')
        with open(caminho_dados, 'r', encoding='utf-8') as arq:
            reader = csv.reader(arq)
            dados = [row for row in reader]
        
        X = [item[1] for item in dados[1:]]
        y = [item[2] for item in dados[1:]]
        print(f'--- aquivo com {len(X)} instâncias')
        print(f'--- rótulos das instâncias:')
        print(f"""{'\n'.join([f"    {item}\t{y.count(item)}" for item in set(y)])}""")

        print('-- Gerando embeddings...')
        X_embed = self.embedder.encode(X, convert_to_numpy=True, show_progress_bar=log_progresso)

        print('-- Treinando classificador...')
        if not pipeline:
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('classificador', LogisticRegression(
                    penalty='l1',
                    solver='saga',
                    C=12.398517892412489,
                    class_weight=None,
                    multi_class='ovr',
                    verbose=1,
                    max_iter=824
                ))
            ])

        # Fit the pipeline on the training data
        if aplica_testes:
            from sklearn.metrics import classification_report
            from sklearn.model_selection import cross_val_predict, StratifiedKFold

            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            y_pred = cross_val_predict(pipeline, X_embed, y, cv=cv, verbose=1)
            metricas_treinamento = classification_report(y, y_pred, output_dict=True)
        
        pipeline.fit(X_embed, y)
        
        self.metadados.update({
            'classes': [str(classe) for classe in pipeline.named_steps['classificador'].classes_],
            "classificador": str(pipeline),
            'metricas_treinamento': metricas_treinamento
        })

        print(f'-- Salvando classificador ({caminho_classificador})')
        joblib.dump(pipeline, caminho_classificador)
        with open(f'{caminho_classificador.replace('.joblib', '_descritor.json')}', 'w', encoding='utf-8') as arq:
            json.dump(self.metadados, arq, ensure_ascii=False, indent=2)

        self.classificador = pipeline
        print('-- Classificador salvo sucesso!')


    def carregar_modelo(self, caminho_classificador:str) -> None:
        print(f'-- Carregando classificador salvo ({caminho_classificador})')
        self.classificador = joblib.load(caminho_classificador)

        with open(caminho_classificador.replace('.joblib', '_descritor.json')) as arq:
            self.metadados = json.load(arq)

        print(f'--- classificador treinado com os rótulos: {', '.join(self.classificador.classes_)}')

    def classificar_intencao(self, texto:str) -> str:
        embeddings = self.embedder.encode([texto])
        return str(self.classificador.predict(embeddings)[0])
    
    def classificar_intencao_proba(self, texto:str) -> Dict[str, float]:
        embeddings = self.embedder.encode([texto])
        probabilidades = self.classificador.predict_proba(embeddings)[0]
        classes = self.classificador.classes_
        return {str(classe): float(probabilidade) for classe, probabilidade in zip(classes, probabilidades)}

    
    def classificar_intencoes(self, textos:List[str]) -> List[str]:
        embeddings = self.embedder.encode(textos)
        return [str(classe) for classe in self.classificador.predict(embeddings)]
    
    def classificar_intencoes_proba(self, textos:List[str]) -> List[ Dict[str, float]]:
        embeddings = self.embedder.encode(textos)
        resultados =  self.classificador.predict_proba(embeddings)
        classes = self.classificador.classes_

        return [
            {str(classe): float(probabilidade) for classe, probabilidade in zip(classes, probabilidades)}
            for probabilidades in resultados
        ]

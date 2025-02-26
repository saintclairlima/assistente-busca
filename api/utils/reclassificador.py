from transformers import BertTokenizer, BertForQuestionAnswering
import torch

from api.configuracoes.config_gerais import configuracoes

class Reclassificador:
    '''
    Classe que pode ser utilizada para realização de reestimação
    '''
    def __init__(self, modelo, tokenizador, device=configuracoes.device, fazer_log=True):
        self.device = device
        self.modelo = modelo
        self.tokenizador = tokenizador
    
    def reclassificar_documento(self, pergunta, texto_documento: str):
        raise NotImplementedError('Método estimar_resposta() não foi implantado para esta classe') 

class ReclassificadorBert(Reclassificador):
    def __init__(self, device=configuracoes.device, fazer_log=True):
        # Carregando modelo e tokenizador pre-treinados
        # optou-se por não usar pipeline, por ser mais lento que usar o modelo diretamente
        if fazer_log: print(f'--- preparando modelo e tokenizador do Bert (usando {configuracoes.embedding_squad_portuguese})...')
        self.device = device
        self.modelo_bert_qa = BertForQuestionAnswering.from_pretrained(configuracoes.embedding_squad_portuguese, cache_dir=configuracoes.url_cache_modelos).to(self.device)
        self.tokenizador_bert = BertTokenizer.from_pretrained(configuracoes.embedding_squad_portuguese, device=self.device, cache_dir=configuracoes.url_cache_modelos)
    
    def reclassificar_documento(self, pergunta, texto_documento: str):
        inputs = self.tokenizador_bert.encode_plus(
            pergunta,
            texto_documento,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )

        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        
        with torch.no_grad():
            outputs = self.modelo_bert_qa(**inputs)

        # AFAZER: Avaliar se score ponderado faz sentido
        # Extraindo os logits como tensores
        logits_inicio = outputs.start_logits
        logits_fim = outputs.end_logits

        # Obtenção dos logits positivos
        logits_inicio_positivos = logits_inicio[0][logits_inicio[0] > 0]
        logits_fim_positivos = logits_fim[0][logits_fim[0] > 0]

        # Média dos logits positivos
        media_logits_inicio_positivos = logits_inicio_positivos.mean().item() if logits_inicio_positivos.numel() > 0 else 0
        media_logits_fim_positivos = logits_fim_positivos.mean().item() if logits_fim_positivos.numel() > 0 else 0

        # Obtendo os índices e valores dos melhores logits
        indice_melhor_logit_inicio = logits_inicio[0].argmax().item()
        melhor_logit_inicio = logits_inicio[0][indice_melhor_logit_inicio].item()

        indice_melhor_logit_fim = logits_fim[0].argmax().item()
        melhor_logit_fim = logits_fim[0][indice_melhor_logit_fim].item()

        # Calcula media_logits_positivos
        media_logits_positivos = (media_logits_inicio_positivos + media_logits_fim_positivos) / 2

        # scores em formato float para serialização com JSON
        score_soma_logits = float(melhor_logit_inicio + melhor_logit_fim)
        score_ponderado = float(score_soma_logits * media_logits_positivos)

        # calculando score estimado
        start_logits_softmax = torch.softmax(logits_inicio, dim=-1)
        end_logits_softmax = torch.softmax(logits_fim, dim=-1)
        score_estimado = float(torch.max(start_logits_softmax).item() * torch.max(end_logits_softmax).item())

        # score: soma do melhor Logit inicial com o melhor logit final
        # score_estimado: multiplicação do softmax dos logits de inicio pelo dos logits de fim
        # -- (manter somente se a performance do score do Bert pelo pipeline ficar lenta)
        # score_ponderado: score ponderado pela média dos logits de inicio e fim, só quando positivos 
        # -- (quanto mais logits positivos, mais o documento tem melhor avaliação)

        tokens_resposta = inputs['input_ids'][0][indice_melhor_logit_inicio:indice_melhor_logit_fim + 1]
        resposta = self.tokenizador_bert.decode(tokens_resposta, skip_special_tokens=True)
        
        return {
            'resposta': resposta,
            'score': (score_estimado, score_soma_logits),
            'score_ponderado': score_ponderado
        }
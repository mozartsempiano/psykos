from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch
from utils import cor
from config import porcentagem_minima, score_min, POS_PATH, NEG_PATH

# inicialização (já no seu filtros.py)
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", use_fast=False)

# conjuntos de prompts
def carregar_prompts(caminho):
    with open(caminho, encoding="utf-8") as f:
        return [linha.strip() for linha in f if linha.strip() and not linha.strip().startswith("#")]

pos = carregar_prompts(POS_PATH)
neg = carregar_prompts(NEG_PATH)
prompts = pos + neg

def avaliar_estetica(image_path):
    image = Image.open(image_path).convert("RGB")
        
    inputs  = clip_processor(text=prompts, images=image, return_tensors="pt", padding=True)
    outputs = clip_model(**inputs)
    logits  = outputs.logits_per_image[0]           # shape [len(prompts)]
    probs   = logits.softmax(dim=0)                 # normaliza entre todos os prompts

    # Filtra prompts com probabilidade baixa
    min_prob = (porcentagem_minima / 100)
    pos_scores = [p for p in probs[:len(pos)] if p > min_prob]
    neg_scores = [p for p in probs[len(pos):] if p > min_prob]

    # Se não sobrou nenhum, evita divisão por zero
    pos_mean = torch.tensor(pos_scores).mean().item() if pos_scores else 0.0
    neg_mean = torch.tensor(neg_scores).mean().item() if neg_scores else 0.0

    # score final: média(pos) / (média(pos)+média(neg))
    if pos_mean + neg_mean == 0:
        beauty_score = 0
    else:
        beauty_score = pos_mean / (pos_mean + neg_mean)
    
    return beauty_score, probs.tolist()

def filtrar_estetica(image_path, url):
    print("\nAvaliando...")

    score, probs = avaliar_estetica(image_path)

    prompt_percents = []
    for prompt, p in zip(prompts, probs):
        pct = int(round(p * 100))
        if pct < porcentagem_minima:  # agora filtra também para o console
            continue
        tag = f"{cor.VERDE}[+]{cor.END}" if prompt in pos else f"{cor.VERMELHO}[-]{cor.END}"
        prompt_percents.append({"prompt": prompt, "percent": pct, "tag": tag})

    # Imprime os prompts ordenados por percentagem decrescente
    for item in sorted(prompt_percents, key=lambda x: x["percent"], reverse=True):
        print(f"  {item['tag']} {item['prompt'][:30]:30s} → {item['percent']:3d}%")

    # Remove o campo 'tag' antes de retornar/salvar
    prompt_percents = [{"prompt": x["prompt"], "percent": x["percent"]} for x in prompt_percents]

    # Score agregado
    score_percent = int(round(score * 100))
    if score >= 0.8:
        color = cor.VERDE
    elif score >= 0.5:
        color = cor.AMARELO
    else:
        color = cor.VERMELHO

    print(f"{color}Score estético: {score_percent}%{cor.END}")

    if (score < (score_min/100)):
        print(f"{cor.AMARELO}Baixo apelo estético.{cor.END} Pulando…")
        return None, prompt_percents

    return score, prompt_percents
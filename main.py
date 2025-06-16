import os
import sys
import time
import io
import random
import requests
import pytesseract
import shutil

from datetime import datetime, timezone
from html import unescape
import re

from PIL import Image
from atproto import Client as BskyClient
from pytumblr import TumblrRestClient

from config import (
    TUMBLR_CONSUMER_KEY,
    TUMBLR_SECRET_KEY,
    TUMBLR_LIST_FILE,
    BLUESKY_HANDLE,
    BLUESKY_APP_PASSWORD,
    TESSERACT_CMD,
    MAX_SIZE,
    QUALIDADE_COMPRIMIDA,
    TEMAS_INDESEJADOS,
    INTERVAL_SECONDS # novo: intervalo em segundos
)
from utils import cor, clean_caption
from filtros import filtrar_estetica
from analytics import salvar_post

# Caminho do executável do Tesseract
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Silenciar warnings
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

try:
    from transformers import logging as hf_logging
    hf_logging.set_verbosity_error()
except ImportError:
    pass  # se transformers não for usado

# Limpar console
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')
    
def limitar_caption(caption, max_len=300):
    # 2 caracteres reservados para as aspas
    limite = max_len - 2
    if len(caption) > limite:
        # Garante que não corte no meio de um caractere especial
        caption = caption[:limite-1].rstrip() + "…"
    return caption

def strip_html(html_text):
    # Substitui <br> e <p> por espaço
    text = re.sub(r'<\s*(br|p)\s*/?>', ' ', html_text, flags=re.IGNORECASE)
    # Remove tags, mas mantém o texto âncora de links
    text = re.sub(r'<a [^>]+>(.*?)</a>', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    return unescape(text).strip()

def load_tumblr_blogs(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = [b.strip() for b in f.read().split(",") if b.strip()]
    return [b if "." in b else f"{b}.tumblr.com" for b in raw]

# Inicializa clientes uma vez
tumblr_client = TumblrRestClient(TUMBLR_CONSUMER_KEY, TUMBLR_SECRET_KEY)
bsky_client   = BskyClient()

def init_bsky():
    bsky_client.login(BLUESKY_HANDLE, BLUESKY_APP_PASSWORD)

# Cache de total_posts por blog
_total_posts_cache = {}
def get_total_posts(blog):
    if blog not in _total_posts_cache:
        info = tumblr_client.posts(blog, type="photo", limit=1)
        _total_posts_cache[blog] = info.get("total_posts", 0)
    return _total_posts_cache[blog]

def get_random_image_from_tumblr():
    blogs = load_tumblr_blogs(TUMBLR_LIST_FILE)
    random.shuffle(blogs)

    for blog in blogs:
        try:
            total = get_total_posts(blog)
            if total < 1:
                continue

            tentativas = min(10, total)  # tente até 10 posts diferentes por blog
            for _ in range(tentativas):
                idx = random.randrange(total)
                resp = tumblr_client.posts(blog, type="photo", limit=1, offset=idx)
                posts = resp.get("posts", [])
                if not posts or not posts[0].get("photos"):
                    continue

                post = posts[0]
                photos = post["photos"]
                num_photos = len(photos)

                # Filtro de tipo de arquivo (exemplo: só jpg e png)
                valid_photos = [p for p in photos if p["original_size"]["url"].lower().endswith(('.jpg', '.jpeg', '.png'))]
                if not valid_photos:
                    continue

                # Seleção das imagens conforme a regra
                if 1 < len(valid_photos) <= 4:
                    urls = [p["original_size"]["url"] for p in valid_photos]
                elif len(valid_photos) > 4:
                    urls = [random.choice(valid_photos)["original_size"]["url"]]
                else:
                    urls = [valid_photos[0]["original_size"]["url"]]

                raw_caption = post.get("caption", "") or ""
                caption = strip_html(raw_caption)
                caption = re.sub(r'[\r\n]+', ' ', caption)

                trail = post.get("trail") or []
                original_link = post.get("post_url")  # fallback padrão

                if trail:
                    op = trail[-1]
                    blog_info = op.get("blog")
                    post_info = op.get("post")
                    if blog_info and post_info:
                        blog_name = blog_info.get("name")
                        post_id = post_info.get("id")
                        if blog_name and post_id:
                            original_link = f"https://{blog_name}.tumblr.com/post/{post_id}"
                    content_raw = op.get("content_raw")
                    if content_raw:
                        caption = strip_html(content_raw)
                        caption = re.sub(r'[\r\n]+', ' ', caption)
                # trail vazio: já está usando o caption do próprio post

                # Remove legenda se sobrou um link explícito (após strip_html)
                print(f"Legenda antes do filtro: {repr(caption)}")
                time.sleep(0.25)
                if re.search(r'https?://\S+|[\w.-]+\.(com|net|org|br|io|gg|xyz)', caption):
                    print("Legenda removida por conter link explícito!")
                    caption = ""
                    time.sleep(0.25)
                print(f"Legenda final: {repr(caption)}")
                time.sleep(0.25)

                # >>> FILTRO DE TEMAS INDESEJADOS <<<
                # if is_unwanted_theme(caption, urls[0]):
                #     print(f"{cor.AMARELO}Tema indesejado detectado na legenda! Pulando post.{cor.END}")
                #     continue

                return urls, caption, original_link, blog

        except Exception as e:
            print(f"Erro ao buscar de {blog}: {e}")
            time.sleep(0.25)
            continue

    raise RuntimeError("Nenhuma imagem válida encontrada em todos os blogs listados.")

# Verifica se a imagem é um placeholder de remoção do Tumblr
def is_removed_placeholder(image_path):
    img = Image.open(image_path).convert("L")
    text = pytesseract.image_to_string(img).lower()
    # regex para caso alguém quebre a frase
    pattern = r"this content has been removed.*for violating"
    if re.search(pattern, text, re.DOTALL):
        return True
    return False

def is_unwanted_theme(caption, image_path):
    print(f"Verificando temas indesejados na legenda e na imagem...")
    time.sleep(0.25)
    # Verifica na legenda
    caption_lower = caption.lower()
    if any(palavra in caption_lower for palavra in TEMAS_INDESEJADOS):
        print("Tema indesejado detectado na legenda!")
        time.sleep(0.25)
        return True
    # Verifica no texto extraído da imagem (OCR)
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img).lower()
        if any(palavra in text for palavra in TEMAS_INDESEJADOS):
            print("Tema indesejado detectado na imagem!")
            time.sleep(0.25)
            return True
    except Exception as e:
        print(f"Erro ao rodar OCR: {e}")
        time.sleep(0.25)
    return False

def is_too_big_head(url):
    try:
        h = requests.head(url, allow_redirects=True, timeout=10)
        size = int(h.headers.get("Content-Length", 0))
        return size > MAX_SIZE
    except Exception:
        return False  # se não conseguir cabeçalho, deixa passar

def limpar_temp():
    if os.path.exists("temp"):
        shutil.rmtree("temp")

def download_to_temp(url):
    os.makedirs("temp", exist_ok=True)
    filename = os.path.basename(url.split("?")[0])
    path = os.path.join("temp", filename)

    r = requests.get(url, stream=True, timeout=15)
    r.raise_for_status()
    with open(path, "wb") as f:
        for chunk in r.iter_content(1024):
            f.write(chunk)

    # Primeiro, comprime a imagem
    try:
        from PIL import Image
        img = Image.open(path)
        img = img.convert("RGB")
        img.save(path, format="JPEG", quality=QUALIDADE_COMPRIMIDA, optimize=True)
    except Exception as e:
        print(f"Erro ao comprimir imagem: {e}")
        time.sleep(0.25)

    # Depois, verifica o tamanho
    size = os.path.getsize(path)
    if size > MAX_SIZE:
        print(f"Arquivo tem {size/1024:.2f} KB (> {MAX_SIZE/1024:.2f} KB). Pulando…")
        time.sleep(0.25)
        # os.remove(path)
        return None

    return path

def shrink_for_nsfw(image_path, max_dim=800):
    print("\nComprimindo...")
    img = Image.open(image_path)
    img.thumbnail((max_dim, max_dim))
    buf = io.BytesIO()
    img = img.convert("RGB")  
    img.save(buf, format="JPEG", quality=QUALIDADE_COMPRIMIDA)
    print(f"{cor.VERDE}Imagem comprimida com sucesso.{cor.END}")
    time.sleep(0.25)
    return buf.getvalue()

# def detect_nsfw(image_path, api_key):    
#     try:
#         small_bytes = shrink_for_nsfw(image_path)
#         print("\nVerificando se é segura...")
#         resp = requests.post(
#             "https://api.deepai.org/api/nsfw-detector",
#             files={'image': ('img.jpg', small_bytes)},
#             headers={'api-key': api_key},
#             timeout=15
#         )
#         data = resp.json()
#         if data.get("output", {}).get("detections"):
#             print(f"\nImagem {cor.VERMELHO}NSFW{cor.END} detectada! Deletando…")
#             os.remove(image_path)
#             return True
#         else:
#             print(f"\n{cor.VERDE}Imagem segura{cor.END}")
#             return False
#     except Exception as e:
#         print(f"\n{cor.VERMELHO}Erro NSFW:{cor.END} {e}")
#         return None

def post_image(image_paths, caption="", original_link=""):
    bsky_client.com.atproto.repo.upload_blob  # garante inicialização
    images = []
    for image_path in image_paths:
        with open(image_path, "rb") as f:
            blob_ref = bsky_client.com.atproto.repo.upload_blob(f.read())
            images.append({"image": blob_ref.blob, "alt": ""})  # alt pode ser customizado

    # Limpa legenda se tiver link
    if re.search(r'https?://\S+|[\w.-]+\.(com|net|org|br|io|gg|xyz)', caption):
        caption = ""

    # caption = "teste" # para debug
    
    caption = limitar_caption(caption)
    
    print(f"\nLegenda recebida em post_image: {repr(caption)}")
    time.sleep(0.25)
    clean = clean_caption(caption)
    print(f"Legenda após clean_caption: {repr(clean)}")
    time.sleep(0.25)
    text_value = clean and f"“{clean}”" or ""
    print(f"Texto final a ser postado: {repr(text_value)}")
    time.sleep(0.25)
    alt_text = clean and f"“{clean}”\n⧉ {original_link}" or f"⧉ {original_link}"

    # Adiciona alt_text em todas as imagens
    for img in images:
        img["alt"] = alt_text
    # Adiciona alt_text só na primeira imagem, se quiser
    # if images:
    #     images[0]["alt"] = alt_text

    record = {
        "$type": "app.bsky.feed.post",
        "text": text_value,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "embed": {
            "$type": "app.bsky.embed.images",
            "images": images
        }
    }

    payload = {
        "repo": bsky_client.me.did,
        "collection": "app.bsky.feed.post",
        "record": record
    }
    res = bsky_client.com.atproto.repo.create_record(data=payload)
    print(f"\n{cor.VERDE}Post efetuado!{cor.END} URI: {res.uri}")

def main():
    if INTERVAL_SECONDS < 60:
        intervalo_str = f"{INTERVAL_SECONDS}s"
    elif INTERVAL_SECONDS < 3600:
        mins = INTERVAL_SECONDS // 60
        secs = INTERVAL_SECONDS % 60
        intervalo_str = f"{mins}m{secs:02d}s" if secs else f"{mins}m"
    else:
        hours = INTERVAL_SECONDS // 3600
        mins = (INTERVAL_SECONDS % 3600) // 60
        secs = INTERVAL_SECONDS % 60
        if mins or secs:
            intervalo_str = f"{hours}h{mins:02d}m{secs:02d}s" if secs else f"{hours}h{mins:02d}m"
        else:
            intervalo_str = f"{hours}h"
    # time.sleep(2)
    print(f"{cor.CIANO}Iniciando bot com intervalo de {intervalo_str}{cor.END}\n")
    init_bsky()
    clear()
    try:
        while True:
            print(f"\n{cor.AZUL}{'-'*48}{cor.END}")
            print(f"{cor.AZUL}Buscando imagem aleatória do Tumblr...{cor.END}")
            urls, caption, original_link, blog = get_random_image_from_tumblr()
            time.sleep(0.25)
            print(f"{cor.VERDE}Imagem(s) encontrada(s):{cor.END} {urls}")
            print(f"{cor.VERDE}Post original:      {cor.END} {original_link}")
            print(f"{cor.VERDE}Blog de origem:     {cor.END} {blog}\n")
            time.sleep(0.25)

            print(f"{cor.AZUL}Baixando imagem(ns)...{cor.END}")
            time.sleep(0.25)
            image_paths = []
            for url in urls:
                if is_too_big_head(url):
                    print(f"{cor.AMARELO}Imagem muito grande, pulando...{cor.END}")
                    salvar_post(
                        url, caption, original_link,
                        blog=blog, rejeitado=True, motivo_rejeicao="Imagem muito grande"
                    )
                    time.sleep(0.25)
                    continue
                image_path = download_to_temp(url)
                if image_path and is_removed_placeholder(image_path):
                    print(f"{cor.AMARELO}Placeholder de remoção detectado! Pulando imagem.{cor.END}")
                    salvar_post(
                        url, caption, original_link,
                        blog=blog, rejeitado=True, motivo_rejeicao="Placeholder de remoção"
                    )
                    time.sleep(0.25)
                    # os.remove(image_path)
                    continue
                if image_path and is_unwanted_theme(caption, image_path):
                    print(f"{cor.AMARELO}Tema indesejado detectado na legenda ou imagem! Pulando imagem.{cor.END}")
                    salvar_post(
                        url, caption, original_link,
                        blog=blog, rejeitado=True, motivo_rejeicao="Tema indesejado"
                    )
                    time.sleep(0.25)
                    # os.remove(image_path)
                    continue
                if image_path:
                    image_paths.append(image_path)
            if not image_paths:
                print(f"{cor.VERMELHO}DEBUG: Erro ao baixar imagens.{cor.END}\n")
                time.sleep(0.25)
                continue

            # print(f"{cor.AMARELO}Verificando NSFW...{cor.END}")
            # bad = detect_nsfw(image_path, NSFW_API_KEY)
            # if bad:
            #     print(f"{cor.VERMELHO}DEBUG: NSFW detectado.{cor.END}\n")
            #     continue

            print(f"{cor.AZUL}Analisando estética da imagem...{cor.END}")
            score, prompt_percents = filtrar_estetica(image_paths[0], urls[0])
            if score is None:
                print(f"{cor.AMARELO}DEBUG: Baixo apelo estético.{cor.END}\n")
                time.sleep(0.25)
                salvar_post(
                    url, caption, original_link,
                    score=None, prompt_percents=prompt_percents,
                    blog=blog, rejeitado=True, motivo_rejeicao="Baixo apelo estético"
                )
                continue

            print(f"{cor.CIANO}\nSalvando histórico do post...{cor.END}")
            salvar_post(urls[0], caption, original_link, score, prompt_percents, blog)
            
            print(f"{cor.AZUL}\nPublicando imagem no Bluesky...{cor.END}")
            post_image(image_paths, caption, original_link)

            print(f"\n{cor.AMARELO}Limpando arquivos temporários...{cor.END}")
            limpar_temp()

            print(f"{cor.CIANO}Aguardando próximo ciclo...{cor.END}")
            for remaining in range(INTERVAL_SECONDS, 0, -1):
                mins, secs = divmod(remaining, 60)
                time_str = f"{mins:02d}:{secs:02d}"
                sys.stdout.write(f"\r{cor.AZUL}Próxima execução em: {time_str} {cor.END}")
                sys.stdout.flush()
                time.sleep(1)
            print()  # pula linha

    except Exception as e:
        print(f"\n{cor.VERMELHO}Erro geral:{cor.END} {e}")

if __name__ == "__main__":
    main()
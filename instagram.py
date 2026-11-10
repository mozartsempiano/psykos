import time

import requests

from config import (
    INSTAGRAM_ACCESS_TOKEN,
    INSTAGRAM_ACCOUNT_ID,
    INSTAGRAM_REEL_BLOGS,
)
from utils import clean_caption

GRAPH_API_ROOT = "https://graph.facebook.com/v27.0"
REQUEST_TIMEOUT = 30
STATUS_POLL_INTERVAL = 60
MAX_STATUS_POLLS = 5
MAX_CAPTION_LENGTH = 2200


def instagram_configured():
    has_account_id = bool(INSTAGRAM_ACCOUNT_ID)
    has_access_token = bool(INSTAGRAM_ACCESS_TOKEN)
    if has_account_id != has_access_token:
        raise RuntimeError(
            "Configure INSTAGRAM_ACCOUNT_ID e INSTAGRAM_ACCESS_TOKEN juntos no .env."
        )
    if has_account_id and not INSTAGRAM_REEL_BLOGS:
        raise RuntimeError(
            "Configure INSTAGRAM_REEL_BLOGS apenas com blogs cujos vídeos você tem "
            "direito de republicar."
        )
    return has_account_id


def _request_json(response, action):
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise RuntimeError(f"Resposta inválida da API do Instagram ao {action}.")
    if "error" in data:
        raise RuntimeError(f"Erro da API do Instagram ao {action}: {data['error']}")
    return data


def post_reel(video_url, caption=""):
    if not instagram_configured():
        raise RuntimeError("Credenciais do Instagram não configuradas.")

    caption = clean_caption(caption)[:MAX_CAPTION_LENGTH].rstrip()
    media_endpoint = f"{GRAPH_API_ROOT}/{INSTAGRAM_ACCOUNT_ID}/media"
    auth_params = {"access_token": INSTAGRAM_ACCESS_TOKEN}

    container_response = requests.post(
        media_endpoint,
        data={
            **auth_params,
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
        },
        timeout=REQUEST_TIMEOUT,
    )
    container = _request_json(container_response, "criar o Reel")
    container_id = container.get("id")
    if not container_id:
        raise RuntimeError("A API do Instagram não retornou o ID do Reel.")

    status_endpoint = f"{GRAPH_API_ROOT}/{container_id}"
    for attempt in range(MAX_STATUS_POLLS):
        status_response = requests.get(
            status_endpoint,
            params={**auth_params, "fields": "status_code"},
            timeout=REQUEST_TIMEOUT,
        )
        status_data = _request_json(status_response, "consultar o processamento do Reel")
        status = status_data.get("status_code")

        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"A API do Instagram não processou o Reel: {status}.")
        if status != "IN_PROGRESS":
            raise RuntimeError(f"Status inesperado do Reel na API do Instagram: {status}.")
        if attempt < MAX_STATUS_POLLS - 1:
            time.sleep(STATUS_POLL_INTERVAL)
    else:
        raise TimeoutError("O Instagram não terminou de processar o Reel após 5 consultas.")

    publish_response = requests.post(
        f"{GRAPH_API_ROOT}/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={**auth_params, "creation_id": container_id},
        timeout=REQUEST_TIMEOUT,
    )
    published = _request_json(publish_response, "publicar o Reel")
    published_id = published.get("id")
    if not published_id:
        raise RuntimeError("A API do Instagram não retornou o ID da publicação.")
    return published_id

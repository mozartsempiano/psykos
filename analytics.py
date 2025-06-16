# Registra histórico de postagens
import json
import os
import time
from config import porcentagem_minima, HISTORY_PATH, REJECTED_PATH
from datetime import datetime, timezone

def salvar_post(url, caption, link, score=None, prompt_percents=None, blog=None, rejeitado=False, motivo_rejeicao=None):
    try:
        path = REJECTED_PATH if rejeitado else HISTORY_PATH

        # Garante que a pasta existe
        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump([], f)

        with open(path, "r") as f:
            data = json.load(f)

        post_data = {
            "url": url,
            "caption": caption,
            "original_link": link,
            "blog": blog,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        print(f"Post {'rejeitado' if rejeitado else 'aprovado'}: {url}")
        time.sleep(0.3)
        if not rejeitado:
            print("\nRegistrando aprovado...")
            time.sleep(0.25)
            post_data["score"] = round(score, 2) if score is not None else None
            if prompt_percents is not None:
                prompt_percents = [
                    {"prompt": x["prompt"], "percent": round(x["percent"])}
                    for x in prompt_percents if x["percent"] > porcentagem_minima
                ]
                prompt_percents = sorted(prompt_percents, key=lambda x: x["percent"], reverse=True)
                post_data["prompt_percents"] = prompt_percents
        else:
            print("\nRegistrando rejeitado...")
            time.sleep(0.25)
            post_data["motivo_rejeicao"] = motivo_rejeicao

        data.append(post_data)

        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Post {'rejeitado' if rejeitado else 'aprovado'} salvo em {path}")
    except Exception as e:
        print(f"Erro ao salvar post: {e}")
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente de um arquivo .env para garantir a segurança das credenciais
load_dotenv()

# Configurações de API - Armazena as credenciais de forma segura em um arquivo .env
# Bluesky
BLUESKY_HANDLE = os.getenv('BLUESKY_HANDLE')
BLUESKY_APP_PASSWORD = os.getenv('BLUESKY_APP_PASSWORD')
# Tumblr
TUMBLR_CONSUMER_KEY = os.getenv("TUMBLR_CONSUMER_KEY")
TUMBLR_SECRET_KEY  = os.getenv("TUMBLR_SECRET_KEY")
# Detector de NSFW
NSFW_API_KEY  = os.getenv("NSFW_API_KEY")

# Configurações do bot
debug_mode = False
INTERVAL_SECONDS = 1800 # Intervalo em segundos.

# Configurações de estética
porcentagem_minima = 3  # Percentagem mínima para considerar um prompt relevante
score_min = 40 # Score mínimo total para considerar uma imagem boa

# Temas indesejados - Evita postagens com esses temas
TEMAS_INDESEJADOS = ["politics", "violence", "gore", "explicit", "nazi", "hitler", "porn", "blood"]

# Caminho do arquivo de lista de Tumblrs
TUMBLR_LIST_FILE = "tumblrs.txt"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# path = os.path.join(BASE_DIR, "tumblr-crawler", "7speakofthedevil7") # Caminho das imagens usadas pelo bot

# Caminho dos arquivos de prompts
PROMPTS_DIR = "prompts"
POS_PATH = os.path.join(PROMPTS_DIR, "prompts_pos.txt")
NEG_PATH = os.path.join(PROMPTS_DIR, "prompts_neg.txt")

# Caminho do histórico de postagens
HISTORY_DIR = "history"
HISTORY_PATH = os.path.join(HISTORY_DIR, "post_history.json")
REJECTED_PATH = os.path.join(HISTORY_DIR, "rejected_posts.json")

# Caminho do tesseract; precisa estar instalado
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe" 

# Configurações de imagem
MAX_SIZE = 976.56 * 1024  # ≈ 1_000_000 bytes
QUALIDADE_COMPRIMIDA = 99  # Qualidade da imagem comprimida (0-100)

# Cores para terminal
class cor:
    VERMELHO = "\033[91m"
    AMARELO = "\033[93m"
    AZUL = "\033[94m"
    VERDE = "\033[92m"
    CIANO = "\033[96m"
    ROXO = "\033[95m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"
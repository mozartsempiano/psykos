import os
import shutil
import time
from datetime import datetime
from config import cor

PYTHONIOENCODING = "UTF-8"

# Centralizar texto
def centralizar(texto):
    largura_tela = shutil.get_terminal_size().columns
    return texto.center(largura_tela)

# Exibir ASCII Art com o título do bot
def exibir_titulo():
    titulo_arquivo = "titulo.txt"
    
    print(cor.VERDE)  # Define a cor do texto pra verde
    
    if os.path.exists(titulo_arquivo):
        with open(titulo_arquivo, encoding=PYTHONIOENCODING) as f:
            for linha in f:
                print(centralizar(linha.strip()))  # Centraliza cada linha do arquivo
    
    # print("\n")
    # print(centralizar("@guizin_botson\n"))
    
    time.sleep(0.5)
    print("\033[0m")  # Restaura a cor padrão

# Retorna hora, dia da semana, mês, ano de hoje
def hoje():
    now = datetime.now()
    
    segundo = str(now.second)
    minuto = str(now.minute)
    hora = str(now.hour)
    dia = str(now.day)
    mes = str(now.month)
    ano = str(now.year)
    
    dias_semana = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
    diaSemana = dias_semana[now.weekday()]
    
    data_hora_formatada = now.strftime('%d/%m/%Y %H:%M:%S')
    print(f"Hoje: {data_hora_formatada} ({diaSemana})\n")
    
    return hora, diaSemana, mes, ano, minuto, segundo

def clean_caption(caption):
    lines = caption.splitlines()
    # Remove a primeira linha só se ela parecer um nome de usuário (opcional)
    # if len(lines) > 1 and lines[0].startswith('@'):
    #     lines = lines[1:]
    # Remove linhas vazias e espaços extras
    lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(lines)

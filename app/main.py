from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import time
import logging
import os

# v15.0.0 - Foco em Persistência e Roteamento Absoluto
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_nome(texto):
    """Garante que o nome do projeto seja processado sem lixo visual"""
    return re.sub(r'\x1b\[[0-9;]*m', '', texto).strip()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None):
    try:
        # Pega a lista oficial do servidor
        result_raw = subprocess.check_output([f"{SCRIPTS_DIR}/listar_projetos.sh"], shell=True).decode()
        projetos = []
        for linha in result_raw.split('\n'):
            l_limpa = limpar_nome(linha)
            if any(s in l_limpa.upper() for s in ["ONLINE", "OFFLINE"]):
                partes = l_limpa.split()
                if len(partes) >= 1:
                    nome_puro = partes[0]
                    projetos.append({
                        "nome": nome_puro,
                        "porta": partes[1] if len(partes) > 1 else "---",
                        "status": "online" if "ONLINE" in l_limpa.upper() else "offline",
                        "url": f"http://34.11.132.26/{nome_puro}/"
                    })
        return templates.TemplateResponse("index.html", {"request": request, "projetos": projetos, "message": msg})
    except Exception as e:
        logger.error(f"Erro ao listar: {e}")
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

@app.post("/remover")
async def remover(nome: str = Form(...)):
    try:
        # Comando de força bruta: garante que o nome vá limpo e confirme S
        nome_valido = "".join(filter(lambda x: x.isalnum() or x in "-_", nome))
        cmd = f"printf '{nome_valido}\nS\n' | sudo {SCRIPTS_DIR}/remover_projeto.sh"
        
        # Execução síncrona aguardando o fim do processo Linux
        os.system(cmd)
        time.sleep(4) # Tempo vital para o Nginx e Systemd estabilizarem
        
        # Redirecionamento absoluto para evitar o erro da imagem f0703f
        return RedirectResponse(url="/orquestrador/", status_code=303)
    except Exception as e:
        return RedirectResponse(url="/orquestrador/?msg=Erro técnico na remoção", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    try:
        nome_limpo = "".join(filter(lambda x: x.isalnum() or x in "-_", nome))
        # printf passa os argumentos na ordem: nome e depois repositório
        cmd = f"printf '{nome_limpo}\n{repo}\n' | sudo {SCRIPTS_DIR}/novo_projeto.sh"
        
        os.system(cmd)
        time.sleep(5) # Aguarda a instalação pesada do app
        return RedirectResponse(url="/orquestrador/", status_code=303)
    except Exception as e:
        return RedirectResponse(url="/orquestrador/?msg=Erro ao criar app", status_code=303)
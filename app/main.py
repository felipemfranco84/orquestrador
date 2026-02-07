from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import time
import logging
import os

# v8.1.1 - Auditoria e Estabilidade [cite: 2026-01-25]
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_nome(texto):
    texto = re.sub(r'\x1b\[[0-9;]*m', '', texto)
    texto = re.sub(r'[^\w\s-]', '', texto)
    return texto.strip()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None, debug_log: str = None):
    try:
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
                        "porta": partes[1] if len(partes) > 1 else "???",
                        "status": "online" if "ONLINE" in l_limpa.upper() else "offline",
                        "url": f"http://34.11.132.26/{nome_puro}/"
                    })
        return templates.TemplateResponse("index.html", {
            "request": request, "projetos": projetos, "message": msg, "debug_log": debug_log
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

@app.get("/auditoria")
async def auditoria():
    """Rota para conferir as pastas reais no servidor sem SSH"""
    try:
        pastas = os.listdir("/home/felicruel/apps")
        return {"status": "sucesso", "pastas_no_servidor": pastas}
    except Exception as e:
        return {"status": "erro", "detalhe": str(e)}

@app.post("/remover")
async def remover(nome: str = Form(...)):
    nome_valido = "".join(filter(lambda x: x.isalnum() or x in "-_", nome))
    cmd = f"printf '{nome_valido}\nS\n' | sudo {SCRIPTS_DIR}/remover_projeto.sh"
    processo = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    time.sleep(3)
    return RedirectResponse(url=f"/?msg=Removido: {nome_valido}&debug_log={processo.stdout}", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    nome_limpo = "".join(filter(lambda x: x.isalnum() or x in "-_", nome))
    cmd = f"printf '{nome_limpo}\n{repo}\n' | sudo {SCRIPTS_DIR}/novo_projeto.sh"
    subprocess.Popen(cmd, shell=True)
    return RedirectResponse(url="/?msg=Iniciado: " + nome_limpo, status_code=303)
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import time
import os
import psutil  # Biblioteca padrão para métricas de sistema

# v16.0.0 - Orquestrador + Telemetria de Recursos [cite: 2026-01-25]
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_nome(texto):
    return re.sub(r'\x1b\[[0-9;]*m', '', texto).strip()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None):
    try:
        # Métricas Globais do Servidor
        stats = {
            "cpu": psutil.cpu_percent(),
            "ram": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent
        }

        result_raw = subprocess.check_output([f"{SCRIPTS_DIR}/listar_projetos.sh"], shell=True).decode()
        projetos = []
        for linha in result_raw.split('\n'):
            l_limpa = limpar_nome(linha)
            if any(s in l_limpa.upper() for s in ["ONLINE", "OFFLINE"]):
                partes = l_limpa.split()
                if len(partes) >= 1:
                    projetos.append({
                        "nome": partes[0],
                        "porta": partes[1] if len(partes) > 1 else "---",
                        "status": "online" if "ONLINE" in l_limpa.upper() else "offline",
                        "url": f"http://34.11.132.26/{partes[0]}/"
                    })
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "projetos": projetos, 
            "message": msg,
            "stats": stats
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

@app.post("/remover")
async def remover(nome: str = Form(...)):
    subprocess.run(f"echo 'S' | sudo {SCRIPTS_DIR}/remover_projeto.sh {nome}", shell=True)
    time.sleep(3)
    return RedirectResponse(url="/orquestrador/", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    subprocess.run(f"printf '{nome}\n{repo}\n' | sudo {SCRIPTS_DIR}/novo_projeto.sh", shell=True)
    time.sleep(4)
    return RedirectResponse(url="/orquestrador/", status_code=303)
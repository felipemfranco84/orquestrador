from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import time
import os
import psutil

# v17.1.0 - Orquestrador com Telemetria em Tempo Real [cite: 2026-01-25]
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_nome(texto):
    """Remove códigos ANSI para processamento correto"""
    return re.sub(r'\x1b\[[0-9;]*m', '', texto).strip()

@app.get("/api/stats")
async def api_stats():
    """Endpoint de telemetria consumido pelo JavaScript"""
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    }

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None):
    try:
        # Snapshot inicial para o carregamento da página
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
            "request": request, "projetos": projetos, "message": msg, "stats": stats
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

@app.post("/remover")
async def remover(nome: str = Form(...)):
    nome_valido = "".join(filter(lambda x: x.isalnum() or x in "-_", nome))
    os.system(f"printf '{nome_valido}\nS\n' | sudo {SCRIPTS_DIR}/remover_projeto.sh")
    time.sleep(4) 
    return RedirectResponse(url="/orquestrador/", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    nome_limpo = "".join(filter(lambda x: x.isalnum() or x in "-_", nome))
    os.system(f"printf '{nome_limpo}\n{repo}\n' | sudo {SCRIPTS_DIR}/novo_projeto.sh")
    time.sleep(5)
    return RedirectResponse(url="/orquestrador/", status_code=303)
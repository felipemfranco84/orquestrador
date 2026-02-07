from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import time
import os

# v9.0.0 - UX Reativa com Transição [cite: 2026-01-25]
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_nome(texto):
    texto = re.sub(r'\x1b\[[0-9;]*m', '', texto)
    return texto.strip()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None):
    try:
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
        return templates.TemplateResponse("index.html", {"request": request, "projetos": projetos, "message": msg})
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

@app.get("/aguarde", response_class=HTMLResponse)
async def aguarde(request: Request, acao: str, tempo: int):
    """Página que segura o usuário enquanto o Linux trabalha"""
    return templates.TemplateResponse("aguarde.html", {"request": request, "acao": acao, "tempo": tempo})

@app.post("/remover")
async def remover(nome: str = Form(...)):
    nome_limpo = "".join(filter(lambda x: x.isalnum() or x in "-_", nome))
    cmd = f"echo 'S' | sudo {SCRIPTS_DIR}/remover_projeto.sh {nome_limpo}"
    subprocess.Popen(cmd, shell=True) # Roda em background
    return RedirectResponse(url=f"/aguarde?acao=Removendo {nome_limpo}&tempo=5", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    nome_limpo = "".join(filter(lambda x: x.isalnum() or x in "-_", nome))
    cmd = f"printf '{nome_limpo}\n{repo}\n' | sudo {SCRIPTS_DIR}/novo_projeto.sh"
    subprocess.Popen(cmd, shell=True) # Roda em background
    return RedirectResponse(url=f"/aguarde?acao=Criando {nome_limpo}&tempo=20", status_code=303)
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import os

# v11.0.0 - Sincronização Assíncrona via Frontend
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_nome(texto):
    return re.sub(r'\x1b\[[0-9;]*m', '', texto).strip()

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
                        "status": "online" if "ONLINE" in l_limpa.upper() else "offline"
                    })
        return templates.TemplateResponse("index.html", {"request": request, "projetos": projetos, "message": msg})
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

@app.get("/status/{nome}")
async def status_projeto(nome: str):
    """API rápida para o navegador saber se o projeto já está pronto"""
    try:
        result = subprocess.check_output([f"{SCRIPTS_DIR}/listar_projetos.sh"], shell=True).decode()
        existe = nome in result
        return {"pronto": existe}
    except:
        return {"pronto": False}

@app.get("/aguarde", response_class=HTMLResponse)
async def aguarde(request: Request, acao: str, nome: str, modo: str):
    # modo: 'criar' (espera aparecer) ou 'remover' (espera sumir)
    return templates.TemplateResponse("aguarde.html", {"request": request, "acao": acao, "nome": nome, "modo": modo})

@app.post("/remover")
async def remover(nome: str = Form(...)):
    nome_limpo = "".join(filter(lambda x: x.isalnum() or x in "-_", nome))
    subprocess.Popen(f"echo 'S' | sudo {SCRIPTS_DIR}/remover_projeto.sh {nome_limpo}", shell=True)
    return RedirectResponse(url=f"/aguarde?acao=Removendo&nome={nome_limpo}&modo=remover", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    nome_limpo = "".join(filter(lambda x: x.isalnum() or x in "-_", nome))
    subprocess.Popen(f"printf '{nome_limpo}\n{repo}\n' | sudo {SCRIPTS_DIR}/novo_projeto.sh", shell=True)
    return RedirectResponse(url=f"/aguarde?acao=Criando&nome={nome_limpo}&modo=criar", status_code=303)
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import os

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_ansi(texto):
    # Remove códigos de cores do terminal para limpar a interface
    return re.sub(r'\x1b\[[0-9;]*m', '', texto)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None):
    result_raw = subprocess.check_output([f"{SCRIPTS_DIR}/listar_projetos.sh"], shell=True).decode()
    projetos_processados = []
    
    for linha in result_raw.split('\n'):
        linha_limpa = limpar_ansi(linha).strip()
        # Filtra apenas linhas úteis com status ONLINE/OFFLINE
        if any(s in linha_limpa for s in ["ONLINE", "OFFLINE"]):
            partes = linha_limpa.split()
            if len(partes) >= 3:
                projetos_processados.append({
                    "nome": partes[0],
                    "porta": partes[1],
                    "status": "online" if "ONLINE" in linha_limpa else "offline",
                    "url": partes[-1] if partes[-1].startswith("http") else "#"
                })
    
    return templates.TemplateResponse("index.html", {"request": request, "projetos": projetos_processados, "message": msg})

@app.post("/remover")
async def remover(nome: str = Form(...)):
    # Executa o script de remoção com confirmação automática
    subprocess.run(f"echo 'S' | {SCRIPTS_DIR}/remover_projeto.sh {nome}", shell=True)
    return RedirectResponse(url=f"/?msg=Projeto {nome} removido", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    cmd = f"printf '{nome}\n{repo}\n' | {SCRIPTS_DIR}/novo_projeto.sh"
    subprocess.Popen(cmd, shell=True)
    return RedirectResponse(url="/?msg=Criando projeto...", status_code=303)
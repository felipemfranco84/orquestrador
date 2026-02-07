from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import time
import os

# v10.0.0 - Sincronização Real de Estado [cite: 2026-01-25]
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_nome(texto):
    return re.sub(r'\x1b\[[0-9;]*m', '', texto).strip()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None):
    try:
        # Pega a lista atualizada do servidor
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
    # Passa os valores explicitamente para evitar o erro da imagem f06443.png
    return templates.TemplateResponse("aguarde.html", {
        "request": request, 
        "acao": acao, 
        "tempo": tempo
    })

@app.post("/remover")
async def remover(nome: str = Form(...)):
    nome_limpo = "".join(filter(lambda x: x.isalnum() or x in "-_", nome))
    # Executa e espera terminar antes de mandar para a página de aguarde
    subprocess.run(f"echo 'S' | sudo {SCRIPTS_DIR}/remover_projeto.sh {nome_limpo}", shell=True)
    return RedirectResponse(url=f"/aguarde?acao=Projeto {nome_limpo} removido&tempo=3", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    nome_limpo = "".join(filter(lambda x: x.isalnum() or x in "-_", nome))
    # Importante: subprocess.run espera o script acabar
    subprocess.run(f"printf '{nome_limpo}\n{repo}\n' | sudo {SCRIPTS_DIR}/novo_projeto.sh", shell=True)
    return RedirectResponse(url=f"/aguarde?acao=Projeto {nome_limpo} criado com sucesso&tempo=5", status_code=303)
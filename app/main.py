from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import time # Adicionado para garantir o refresh correto

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_ansi(texto):
    return re.sub(r'\x1b\[[0-9;]*m', '', texto)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None):
    result_raw = subprocess.check_output([f"{SCRIPTS_DIR}/listar_projetos.sh"], shell=True).decode()
    projetos = []
    for linha in result_raw.split('\n'):
        l = limpar_ansi(linha).strip()
        if any(s in l for s in ["ONLINE", "OFFLINE"]):
            p = l.split()
            if len(p) >= 3:
                projetos.append({
                    "nome": p[0], "porta": p[1],
                    "status": "online" if "ONLINE" in l else "offline",
                    # Recuperando a URL correta para o botão Abrir
                    "url": p[-1] if p[-1].startswith("http") else f"http://34.11.132.26/{p[0]}/"
                })
    return templates.TemplateResponse("index.html", {"request": request, "projetos": projetos, "message": msg})

@app.post("/remover")
async def remover(nome: str = Form(...)):
    subprocess.run(f"echo 'S' | {SCRIPTS_DIR}/remover_projeto.sh {nome}", shell=True)
    time.sleep(2) # Pausa estratégica para o Linux processar a exclusão
    return RedirectResponse(url=f"./?msg=Projeto {nome} removido com sucesso", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    subprocess.Popen(f"printf '{nome}\n{repo}\n' | {SCRIPTS_DIR}/novo_projeto.sh", shell=True)
    return RedirectResponse(url="./?msg=Criando projeto... verifique a lista em 15s", status_code=303)
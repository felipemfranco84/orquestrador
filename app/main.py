from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import logging

# v7.2.0 - Correção de Rotas e Limpeza ANSI [cite: 2026-01-25]
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_ansi(texto):
    """Remove o lixo visual [34m que aparece na imagem image_ef7f05"""
    return re.sub(r'\x1b\[[0-9;]*m', '', texto)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None):
    try:
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
                        "url": p[-1] if p[-1].startswith("http") else "#"
                    })
        return templates.TemplateResponse("index.html", {"request": request, "projetos": projetos, "message": msg})
    except Exception as e:
        logger.error(f"Erro: {e}")
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

@app.post("/remover")
async def remover(nome: str = Form(...)):
    # Executa remoção automática
    subprocess.run(f"echo 'S' | {SCRIPTS_DIR}/remover_projeto.sh {nome}", shell=True)
    return RedirectResponse(url="./?msg=Projeto removido", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    subprocess.Popen(f"printf '{nome}\n{repo}\n' | {SCRIPTS_DIR}/novo_projeto.sh", shell=True)
    return RedirectResponse(url="./?msg=Criando projeto...", status_code=303)
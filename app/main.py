from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import logging

# Log de decisão: Simplificação total para evitar travamento de UI [cite: 2026-01-25]
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_nome(texto):
    """Remove sujeira de terminal para o HTML"""
    return re.sub(r'\x1b\[[0-9;]*m', '', texto).strip()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None):
    try:
        # Pega a lista real. Se o projeto foi criado/removido, ele já aparece/some aqui
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
        logger.error(f"Erro na home: {e}")
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

@app.post("/remover")
async def remover(nome: str = Form(...)):
    # O navegador vai aguardar aqui até o script terminar
    subprocess.run(f"echo 'S' | sudo {SCRIPTS_DIR}/remover_projeto.sh {nome}", shell=True)
    return RedirectResponse(url="/?msg=Projeto removido com sucesso", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    # O navegador aguarda a criação (instalação de dependências)
    subprocess.run(f"printf '{nome}\n{repo}\n' | sudo {SCRIPTS_DIR}/novo_projeto.sh", shell=True)
    return RedirectResponse(url=f"/?msg=Projeto {nome} criado e pronto", status_code=303)
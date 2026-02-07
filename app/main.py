from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import time
import logging

# Configuração MAJOR.MINOR.PATCH: v7.5.0 [cite: 2026-01-25]
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_ansi(texto):
    """Limpa a sujeira visual [34m vista na imagem image_ef7f05"""
    return re.sub(r'\x1b\[[0-9;]*m', '', texto)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None):
    try:
        # Pega a lista real de processos do servidor
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
                        "url": f"http://34.11.132.26/{p[0]}/"
                    })
        return templates.TemplateResponse("index.html", {"request": request, "projetos": projetos, "message": msg})
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

@app.post("/remover")
async def remover(nome: str = Form(...)):
    try:
        # FORÇA BRUTA: echo S + sudo + caminho absoluto
        # O 'sudo -n' garante que ele falhe rápido se pedir senha, em vez de travar o site
        cmd = f"echo 'S' | sudo -n {SCRIPTS_DIR}/remover_projeto.sh {nome}"
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        
        time.sleep(3) # Tempo para o Linux apagar as pastas e o Nginx recarregar
        return RedirectResponse(url=f"./?msg=Projeto {nome} removido com sucesso", status_code=303)
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro Shell: {e.stderr.decode()}")
        return RedirectResponse(url=f"./?msg=Erro técnico ao remover {nome}", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    # Criar em background para a página não ficar 'girando'
    cmd = f"printf '{nome}\n{repo}\n' | sudo -n {SCRIPTS_DIR}/novo_projeto.sh"
    subprocess.Popen(cmd, shell=True)
    return RedirectResponse(url="./?msg=Criando projeto... verifique a lista em 15s", status_code=303)
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import time
import logging

# v7.6.0 - Edição Especial de Diagnóstico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_ansi(texto):
    """Remove o lixo visual [34m visto na imagem image_ef7f05"""
    return re.sub(r'\x1b\[[0-9;]*m', '', texto)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None, debug_log: str = None):
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
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "projetos": projetos, 
            "message": msg,
            "debug_log": debug_log # Enviando o log técnico para a tela
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

@app.post("/remover")
async def remover(nome: str = Form(...)):
    try:
        logger.info(f"Tentando remover projeto: {nome}")
        # Capturamos toda a conversa do terminal para descobrir o erro
        cmd = f"echo 'S' | sudo {SCRIPTS_DIR}/remover_projeto.sh {nome}"
        processo = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # Unimos o que deu certo e o que deu errado para diagnóstico
        full_log = f"LOG DE SAÍDA:\n{processo.stdout}\n\nLOG DE ERRO:\n{processo.stderr}"
        
        time.sleep(3)
        return RedirectResponse(url=f"/?msg=Executado: {nome}&debug_log={full_log}", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/?msg=Erro Crítico&debug_log={str(e)}", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    # Criar em background para a página não travar
    cmd = f"printf '{nome}\n{repo}\n' | sudo {SCRIPTS_DIR}/novo_projeto.sh"
    subprocess.Popen(cmd, shell=True)
    return RedirectResponse(url="/?msg=Criando projeto... verifique a lista em 15s", status_code=303)
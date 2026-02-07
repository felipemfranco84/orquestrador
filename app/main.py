from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import time
import logging

# v7.7.0 - Versão "Nome Limpo" [cite: 2026-01-25]
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_ansi(texto):
    """Remove códigos de cor ANSI para evitar nomes de arquivos inválidos"""
    return re.sub(r'\x1b\[[0-9;]*m', '', texto)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None, debug_log: str = None):
    try:
        result_raw = subprocess.check_output([f"{SCRIPTS_DIR}/listar_projetos.sh"], shell=True).decode()
        projetos = []
        for linha in result_raw.split('\n'):
            l_limpa = limpar_ansi(linha).strip()
            
            if any(s in l_limpa for s in ["ONLINE", "OFFLINE"]):
                partes = l_limpa.split()
                if len(partes) >= 3:
                    # O segredo está em limpar o nome aqui
                    nome_puro = partes[0]
                    projetos.append({
                        "nome": nome_puro,
                        "porta": partes[1],
                        "status": "online" if "ONLINE" in l_limpa else "offline",
                        "url": f"http://34.11.132.26/{nome_puro}/"
                    })
        return templates.TemplateResponse("index.html", {
            "request": request, "projetos": projetos, "message": msg, "debug_log": debug_log
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

@app.post("/remover")
async def remover(nome: str = Form(...)):
    try:
        # Garante que o nome não tenha espaços ou lixo
        nome_valido = nome.strip()
        cmd = f"echo 'S' | sudo {SCRIPTS_DIR}/remover_projeto.sh {nome_valido}"
        processo = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        full_log = f"LOG DE SAÍDA:\n{processo.stdout}\n\nLOG DE ERRO:\n{processo.stderr}"
        time.sleep(3)
        return RedirectResponse(url=f"/?msg=Executado: {nome_valido}&debug_log={full_log}", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/?msg=Erro Crítico&debug_log={str(e)}", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    cmd = f"printf '{nome}\n{repo}\n' | sudo {SCRIPTS_DIR}/novo_projeto.sh"
    subprocess.Popen(cmd, shell=True)
    return RedirectResponse(url="/?msg=Criando projeto...", status_code=303)
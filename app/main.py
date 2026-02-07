from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import re
import time
import logging
import os

# v8.0.0 - Normalização de Nomes e Caminhos [cite: 2026-01-25]
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"
APPS_DIR = "/home/felicruel/apps"

def limpar_nome(texto):
    """Remove cores ANSI e qualquer caractere invisível ou de controle"""
    texto = re.sub(r'\x1b\[[0-9;]*m', '', texto) # Remove ANSI
    texto = re.sub(r'[^\w\s-]', '', texto) # Mantém apenas letras, números, hífens e sublinhados
    return texto.strip()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None, debug_log: str = None):
    try:
        result_raw = subprocess.check_output([f"{SCRIPTS_DIR}/listar_projetos.sh"], shell=True).decode()
        projetos = []
        for linha in result_raw.split('\n'):
            l_limpa = limpar_nome(linha)
            if any(s in l_limpa.upper() for s in ["ONLINE", "OFFLINE"]):
                partes = l_limpa.split()
                if len(partes) >= 1:
                    nome_puro = partes[0]
                    # Tenta capturar a porta se existir, senão usa padrão
                    porta = partes[1] if len(partes) > 1 and partes[1].isdigit() else "???"
                    status = "online" if "ONLINE" in l_limpa.upper() else "offline"
                    
                    projetos.append({
                        "nome": nome_puro,
                        "porta": porta,
                        "status": status,
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
        # Sanitização extrema do nome para o Shell
        nome_valido = "".join(filter(lambda x: x.isalnum() or x in "-_", nome))
        
        # Verificamos se o script existe antes de rodar
        script_path = f"{SCRIPTS_DIR}/remover_projeto.sh"
        
        # Comando usando printf para garantir a ordem dos inputs
        cmd = f"printf '{nome_valido}\nS\n' | sudo {script_path}"
        processo = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        full_log = f"BUSCA POR: '{nome_valido}'\n\nSAÍDA LINUX:\n{processo.stdout}\n\nERRO LINUX:\n{processo.stderr}"
        time.sleep(2)
        return RedirectResponse(url=f"/?msg=Processado: {nome_valido}&debug_log={full_log}", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/?msg=Erro Crítico&debug_log={str(e)}", status_code=303)

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    nome_limpo = "".join(filter(lambda x: x.isalnum() or x in "-_", nome))
    cmd = f"printf '{nome_limpo}\n{repo}\n' | sudo {SCRIPTS_DIR}/novo_projeto.sh"
    subprocess.Popen(cmd, shell=True)
    return RedirectResponse(url="/?msg=Iniciado: " + nome_limpo, status_code=303)
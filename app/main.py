from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import logging
import re

# Padrão MAJOR.MINOR.PATCH: v6.9.1
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
SCRIPTS_DIR = "/home/felicruel/scripts"

def limpar_ansi(texto):
    """Remove códigos de escape do terminal (ex: [32m) para limpar o HTML"""
    return re.sub(r'\x1b\[[0-9;]*m', '', texto)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None):
    try:
        # Executa o script original de listagem
        result_raw = subprocess.check_output([f"{SCRIPTS_DIR}/listar_projetos.sh"], shell=True).decode()
        
        projetos_processados = []
        for linha in result_raw.split('\n'):
            linha_limpa = limpar_ansi(linha).strip()
            
            # Filtra apenas linhas que são de fato projetos (contém ONLINE ou OFFLINE)
            if any(s in linha_limpa for s in ["ONLINE", "OFFLINE"]):
                partes = linha_limpa.split()
                if len(partes) >= 3:
                    projetos_processados.append({
                        "nome": partes[0],
                        "porta": partes[1],
                        "status": "online" if "ONLINE" in linha_limpa else "offline",
                        "url": partes[-1] if partes[-1].startswith("http") else "#"
                    })
        
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "projetos": projetos_processados, 
            "message": msg
        })
    except Exception as e:
        logger.error(f"Erro ao processar portal: {str(e)}")
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    try:
        # Envia os dados para o script shell via pipe
        cmd = f"printf '{nome}\n{repo}\n' | {SCRIPTS_DIR}/novo_projeto.sh"
        subprocess.Popen(cmd, shell=True)
        return RedirectResponse(url="/?msg=Iniciando criação do app...", status_code=303)
    except Exception as e:
        logger.error(f"Erro na criação: {str(e)}")
        return RedirectResponse(url=f"/?msg=Erro: {str(e)}", status_code=303)

@app.post("/remover")
async def remover(nome: str = Form(...)):
    try:
        # Exec
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import subprocess
import logging
import os

# Padrão MAJOR.MINOR.PATCH: v6.8.0
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

SCRIPTS_DIR = "/home/felicruel/scripts"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, msg: str = None):
    try:
        # Executa o script de listagem e captura a saída
        # O script original retorna o status dos serviços
        result = subprocess.check_output([f"{SCRIPTS_DIR}/listar_projetos.sh"], shell=True).decode()
        
        # Tratamento simples para transformar a string em lista para o HTML
        linhas = [l.strip() for l in result.split('\n') if l.strip() and not l.startswith('---')]
        
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "projetos": linhas, 
            "message": msg
        })
    except Exception as e:
        logger.error(f"Erro ao listar: {str(e)}")
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

@app.post("/criar")
async def criar(nome: str = Form(...), repo: str = Form(...)):
    try:
        # Envia os inputs para o script de criação via pipe
        cmd = f"printf '{nome}\n{repo}\n' | {SCRIPTS_DIR}/novo_projeto.sh"
        subprocess.Popen(cmd, shell=True)
        return RedirectResponse(url="/?msg=Criando projeto... aguarde 10s", status_code=303)
    except Exception as e:
        logger.error(f"Falha na criacao: {str(e)}")
        return RedirectResponse(url=f"/?msg=Erro: {str(e)}", status_code=303)

@app.post("/remover")
async def remover(nome: str = Form(...)):
    try:
        # Executa a remoção automática respondendo 'S' ao prompt
        cmd = f"echo 'S' | {SCRIPTS_DIR}/remover_projeto.sh {nome}"
        subprocess.run(cmd, shell=True)
        return RedirectResponse(url=f"/?msg=Projeto {nome} removido", status_code=303)
    except Exception as e:
        logger.error(f"Erro ao remover: {str(e)}")
        return RedirectResponse(url="/?msg=Erro ao remover", status_code=303)
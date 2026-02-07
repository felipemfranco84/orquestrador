from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import subprocess
import os
import logging

# Configuração de Logs conforme padrão MAJOR.MINOR.PATCH [cite: 2026-01-25]
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

SCRIPTS_PATH = "/home/felicruel/scripts"

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Chama o script de listagem para exibir no painel
    result = subprocess.check_output([f"{SCRIPTS_PATH}/listar_projetos.sh"], shell=True).decode()
    return templates.TemplateResponse("index.html", {"request": request, "projetos": result})

@app.post("/criar", response_class=HTMLResponse)
async def criar_projeto(request: Request, nome: str = Form(...), repo: str = Form(...)):
    try:
        # Executa o script de criação via web
        command = f"{SCRIPTS_PATH}/novo_projeto.sh <<EOF\n{nome}\n{repo}\nEOF"
        subprocess.Popen(command, shell=True)
        
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "message": f"Projeto {nome} sendo criado! Siga o manual abaixo para o Webhook.",
            "show_manual": True,
            "nome_projeto": nome
        })
    except Exception as e:
        logger.error(f"Erro na criação: {str(e)}")
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

# Bloco try/except obrigatório conforme Cérebro [cite: 2026-01-25]
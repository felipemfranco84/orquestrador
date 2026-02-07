@app.post("/remover")
async def remover(nome: str = Form(...)):
    try:
        logger.info(f"🔥 Solicitando remoção forçada do projeto: {nome}")
        
        # Comando reforçado: usa o caminho completo do sudo e força a entrada
        cmd = f"echo 'S' | sudo /home/felicruel/scripts/remover_projeto.sh {nome}"
        
        # Usamos .run para garantir que o Python espere o script terminar [cite: 2026-01-25]
        subprocess.run(cmd, shell=True, check=True)
        
        # Aumentamos o sleep para 3s para o Systemd processar o desligamento
        time.sleep(3) 
        
        return RedirectResponse(url=f"./?msg=Projeto {nome} removido com sucesso", status_code=303)
    except Exception as e:
        logger.error(f"❌ Falha crítica ao remover {nome}: {str(e)}")
        return RedirectResponse(url=f"./?msg=Erro ao remover: {nome}", status_code=303)
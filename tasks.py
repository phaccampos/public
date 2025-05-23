import time
import logging

# Certifique-se que o logger usado aqui seja o mesmo configurado em app.py
# ou que ele propague para o logger raiz.
# Para simplicidade, podemos pegar o logger raiz.
logger = logging.getLogger() # Pega o logger raiz

def example_task_success():
    logger.info("Executando example_task_success...")
    time.sleep(2) # Simula algum trabalho
    logger.info("example_task_success concluída com sucesso.")
    return "Resultado de example_task_success"

def example_task_failure():
    logger.info("Executando example_task_failure...")
    time.sleep(1) # Simula algum trabalho
    raise ValueError("Simulação de falha em example_task_failure")

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, JobExecutionEvent # Adicionado para monitoramento
from sqlalchemy import create_engine # Adicionada conforme solicitado na tarefa
from flask import Flask, render_template_string, redirect, url_for, flash # Adicionado redirect, url_for, flash
import threading # Para rodar o Flask em uma thread separada
import os # Para getenv e flask_app.secret_key
from datetime import datetime

from email_notifications import send_email # Adicionado para notificações por email

import time # Adicionado para o loop principal e exemplos
# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ENABLE_EMAIL_NOTIFICATIONS = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'False').lower() == 'true'

flask_app = Flask(__name__)
flask_app.secret_key = os.urandom(24) # Necessário para flash messages

DATABASE_URL = "sqlite:///jobs.sqlite"

jobstores = {
    'default': SQLAlchemyJobStore(url=DATABASE_URL)
}

scheduler = BackgroundScheduler(jobstores=jobstores)

# Funções Listener de Eventos
def job_listener_success(event: JobExecutionEvent):
    if event:
        log_message = f"Job {event.job_id} executado com sucesso. Retorno: {event.retval}"
        logging.info(log_message)
        if ENABLE_EMAIL_NOTIFICATIONS:
            email_subject = f"SUCESSO: Tarefa {event.job_id} Concluída"
            email_body = f"A tarefa {event.job_id} foi executada com sucesso.\n\nRetorno:\n{event.retval}"
            send_email(email_subject, email_body) # Envia para DEFAULT_RECEIVER_EMAIL
    else:
        logging.info("Listener de sucesso chamado sem evento.") # Mantido para caso o evento seja None

def job_listener_error(event: JobExecutionEvent):
    if event:
        log_message = f"Job {event.job_id} falhou. Exceção: {event.exception}\nTraceback: {event.traceback}"
        logging.error(log_message) # Log original mantido
        if ENABLE_EMAIL_NOTIFICATIONS:
            email_subject = f"FALHA: Tarefa {event.job_id} Erro na Execução"
            email_body = f"A tarefa {event.job_id} falhou durante a execução.\n\nExceção:\n{event.exception}\n\nTraceback:\n{event.traceback}"
            send_email(email_subject, email_body) # Envia para DEFAULT_RECEIVER_EMAIL
    else:
        logging.error("Listener de erro chamado sem evento.") # Mantido para caso o evento seja None

# Adicionar Listeners ao Scheduler
scheduler.add_listener(job_listener_success, EVENT_JOB_EXECUTED)
scheduler.add_listener(job_listener_error, EVENT_JOB_ERROR)

def add_job_to_scheduler(job_id, func_path, trigger_args, replace_existing=True):
    logging.info(f"Adicionando/atualizando job: {job_id}, func: {func_path}, trigger: {trigger_args}")
    try:
        scheduler.add_job(
            func_path,
            id=job_id,
            replace_existing=replace_existing,
            **trigger_args  # Desempacota os argumentos do trigger aqui
        )
        logging.info(f"Job {job_id} adicionado/atualizado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao adicionar/atualizar job {job_id}: {e}")

def remove_job_from_scheduler(job_id):
    logging.info(f"Tentando remover job: {job_id}")
    try:
        scheduler.remove_job(job_id)
        logging.info(f"Job {job_id} removido com sucesso.")
    except Exception as e: # Especificamente, pode ser apscheduler.jobstores.base.JobLookupError
        logging.error(f"Erro ao remover job {job_id} (pode não existir): {e}")

def list_scheduled_jobs():
    logging.info("Listando jobs agendados...")
    jobs_info = []
    try:
        for job in scheduler.get_jobs():
            job_info = {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            jobs_info.append(job_info)
            logging.debug(f"Job: {job_info}") # Log detalhado de cada job
        logging.info(f"Total de jobs listados: {len(jobs_info)}")
    except Exception as e:
        logging.error(f"Erro ao listar jobs: {e}")
    return jobs_info

@flask_app.route('/')
def index():
    jobs = list_scheduled_jobs()
    
    # Construir HTML com mensagens flash e botão de execução manual
    html = """
    <html>
        <head>
            <title>Tarefas Agendadas</title>
            <style>
                .alert { padding: 15px; margin-bottom: 20px; border: 1px solid transparent; border-radius: 4px; }
                .alert-success { color: #155724; background-color: #d4edda; border-color: #c3e6cb; }
                .alert-error { color: #721c24; background-color: #f8d7da; border-color: #f5c6cb; }
            </style>
        </head>
        <body>
            <h1>Tarefas Agendadas</h1>
            {% with messages = get_flashed_messages(with_categories=true) %}
              {% if messages %}
                {% for category, message in messages %}
                  <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
              {% endif %}
            {% endwith %}
    """
    if not jobs:
        html += "<p>Nenhuma tarefa agendada.</p>"
    else:
        html += "<table border='1'><tr><th>ID</th><th>Função</th><th>Próxima Execução</th><th>Ações</th></tr>"
        for job in jobs:
            job_id = job.get('id', 'N/A')
            job_name = job.get('name', 'N/A')
            next_run = job.get('next_run_time', 'N/A')
            # Adicionar link/botão para execução manual
            run_link = f"<a href='{url_for('run_job', job_id=job_id)}'>Executar Agora</a>"
            html += f"<tr><td>{job_id}</td><td>{job_name}</td><td>{next_run}</td><td>{run_link}</td></tr>"
        html += "</table>"
    html += "</body></html>"
    return render_template_string(html)

@flask_app.route('/job/run/<job_id>')
def run_job(job_id):
    try:
        original_job = scheduler.get_job(job_id, jobstore='default') # Busca o job original
        
        if original_job:
            # Gera um ID único para esta execução manual
            manual_run_id = f"{job_id}_manual_{os.urandom(4).hex()}"
            
            logging.info(f"Tentando executar manualmente o job '{job_id}' como um novo job temporário '{manual_run_id}'.")
            
            # Adiciona um NOVO job baseado no original, mas para rodar imediatamente
            scheduler.add_job(
                func=original_job.func,       # A mesma função do job original
                args=original_job.args,       # Os mesmos argumentos
                kwargs=original_job.kwargs,   # Os mesmos argumentos chave-valor
                trigger='date',               # Para rodar apenas uma vez
                run_date=datetime.now(scheduler.timezone), # Data/hora atual, usando o timezone do scheduler
                id=manual_run_id,             # ID único para esta execução
                name=f"{original_job.name} (Execução Manual)", # Nome descritivo
                jobstore='default',
                replace_existing=False        # Não substitui nenhum job existente
            )
            
            flash(f"Tarefa '{job_id}' (como '{manual_run_id}') foi agendada para execução imediata com sucesso!", 'success')
            logging.info(f"Job '{job_id}' (como '{manual_run_id}') agendado para execução manual imediata.")
        else:
            flash(f"Tarefa '{job_id}' não encontrada no agendador.", 'error')
            logging.warning(f"Tentativa de executar manualmente o job '{job_id}', mas ele não foi encontrado.")
            
    except Exception as e:
        flash(f"Erro ao tentar executar a tarefa '{job_id}': {str(e)}", 'error')
        logging.error(f"Erro ao disparar manualmente o job '{job_id}': {e}", exc_info=True)
        
    return redirect(url_for('index'))

def run_flask_app():
    # host='0.0.0.0' para tornar acessível na rede local
    # use_reloader=False é importante para evitar problemas com o scheduler rodando duas vezes
    flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    logging.info("Iniciando a aplicação...")
    # Listeners já foram adicionados acima, antes de start()
    scheduler.start()
    logging.info("Agendador APScheduler iniciado.")

    # Agendar tarefas de exemplo (como já está)
    add_job_to_scheduler(
        job_id="task_success_1",
        func_path="tasks.example_task_success",
        trigger_args={'trigger': 'interval', 'seconds': 10}
    )
    add_job_to_scheduler(
        job_id="task_failure_1",
        func_path="tasks.example_task_failure",
        trigger_args={'trigger': 'interval', 'seconds': 15}
    )

    jobs = list_scheduled_jobs()
    for job_info in jobs:
        logging.info(f"Job Agendado: {job_info}")

    # Iniciar Flask em uma thread separada
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    logging.info("Servidor Flask iniciado em http://localhost:5000. Pressione Ctrl+C para sair.")

    try:
        # Mantenha o script principal rodando (o scheduler já está em background)
        while True:
            time.sleep(2) # Loop principal pode dormir mais
    except (KeyboardInterrupt, SystemExit):
        logging.info("Aplicação principal parando...")
    finally:
        logging.info("Parando o agendador APScheduler...")
        scheduler.shutdown()
        logging.info("Agendador APScheduler parado.")
        # A thread do Flask é daemon, então ela vai parar quando o programa principal sair.

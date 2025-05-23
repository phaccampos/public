import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys
import time

# Adicionar o diretório raiz ao sys.path para encontrar os módulos app e tasks
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importações do módulo app (precisam ser depois do sys.path.insert)
import app 
from app import scheduler, flask_app, add_job_to_scheduler, remove_job_from_scheduler, list_scheduled_jobs
from tasks import example_task_success, example_task_failure # Para ter uma função real para agendar
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.events import JobExecutionEvent

class TestSchedulerApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Parar o scheduler principal se estiver rodando e reconfigurar
        if scheduler.running:
            scheduler.shutdown(wait=False)
        
        cls.original_jobstores = scheduler.options.jobstores
        # Configurar MemoryJobStore para os testes
        scheduler.configure(jobstores={'default': MemoryJobStore()}, 
                            job_defaults={'coalesce': False, 'max_instances': 3})
        
        # O scheduler é iniciado no setUp de cada teste individualmente se necessário.
        # scheduler.start(paused=True) # Não iniciar globalmente aqui, mas no setUp individual ou no teste.

    @classmethod
    def tearDownClass(cls):
        if scheduler.running:
            scheduler.shutdown(wait=True) # Esperar jobs terminarem
        # Restaurar jobstores originais pode ser complexo se o scheduler original tiver que ser reiniciado.
        # Por simplicidade, para este contexto, vamos apenas garantir que ele pare.
        # scheduler.options.jobstores = cls.original_jobstores 
        # Se o scheduler original precisa ser restaurado e reiniciado, seria necessário mais código.
        # Para este escopo, vamos assumir que após os testes, o estado do scheduler importado não precisa ser restaurado para um estado de execução.
        # Se app.py fosse re-executado, ele reconfiguraria o scheduler com o jobstore de arquivo.

    def setUp(self):
        # Limpar jobs antes de cada teste
        if scheduler.running: # Pausar antes de remover jobs para evitar execuções durante a limpeza
            scheduler.pause()
        scheduler.remove_all_jobs()

        # Garantir que o scheduler esteja rodando para cada teste
        # O estado 1 é STATE_RUNNING, 2 é STATE_PAUSED.
        if not scheduler.running:
            scheduler.start(paused=False) # Iniciar e garantir que não está pausado
        elif scheduler.state == 2: # STATE_PAUSED = 2
            scheduler.resume()
        
        self.client = flask_app.test_client()
        flask_app.config['TESTING'] = True
        # Restaurar o valor de ENABLE_EMAIL_NOTIFICATIONS para o padrão do ambiente,
        # pois alguns testes podem alterá-lo.
        app.ENABLE_EMAIL_NOTIFICATIONS = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'False').lower() == 'true'


    def tearDown(self):
        if scheduler.running:
            scheduler.pause() # Pausar para limpar jobs sem que eles disparem
        scheduler.remove_all_jobs()
        # Não desligar o scheduler aqui, pois o setUpClass/tearDownClass lida com o ciclo de vida geral.
        # Se o scheduler fosse iniciado/parado em cada teste, isso poderia levar a problemas de concorrência ou lentidão.


    def test_add_and_list_job(self):
        job_id = "test_job_1"
        add_job_to_scheduler(
            job_id=job_id,
            func_path="tasks.example_task_success",
            trigger_args={'trigger': 'interval', 'seconds': 60} # Intervalo longo para não rodar durante o teste
        )
        
        jobs = list_scheduled_jobs()
        self.assertTrue(any(job['id'] == job_id for job in jobs))
        job_info = next((job for job in jobs if job['id'] == job_id), None)
        self.assertIsNotNone(job_info)
        self.assertEqual(job_info['name'], "tasks.example_task_success")

    def test_remove_job(self):
        job_id = "test_job_to_remove"
        add_job_to_scheduler(
            job_id=job_id,
            func_path="tasks.example_task_success",
            trigger_args={'trigger': 'interval', 'seconds': 60}
        )
        
        remove_job_from_scheduler(job_id)
        
        jobs = list_scheduled_jobs()
        self.assertFalse(any(job['id'] == job_id for job in jobs))

    def test_flask_index_route_no_jobs(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Nenhuma tarefa agendada", response.data)

    def test_flask_index_route_with_jobs(self):
        job_id = "flask_test_job"
        add_job_to_scheduler(
            job_id=job_id,
            func_path="tasks.example_task_success",
            trigger_args={'trigger': 'date', 'run_date': '2099-01-01T12:00:00Z'} # Data distante
        )
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(job_id, 'utf-8'), response.data)
        self.assertIn(b"tasks.example_task_success", response.data)

    @patch('app.send_email') # Mock a função send_email no módulo app
    def test_email_notification_on_success(self, mock_send_email):
        app.ENABLE_EMAIL_NOTIFICATIONS = True
        
        mock_event = MagicMock(spec=JobExecutionEvent)
        mock_event.job_id = "test_success_job_email"
        mock_event.retval = "Success result from test"
        
        # Chamar o listener diretamente com o evento mockado
        app.job_listener_success(mock_event)
        
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        self.assertIn("SUCESSO: Tarefa test_success_job_email", args[0]) # Checar assunto
        self.assertIn("executada com sucesso", args[1]) # Checar corpo
        self.assertIn("Success result from test", args[1])

        # Restaurar para o valor original baseado no ambiente
        app.ENABLE_EMAIL_NOTIFICATIONS = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'False').lower() == 'true'

    @patch('app.send_email') # Mock a função send_email no módulo app
    def test_email_notification_on_failure(self, mock_send_email):
        app.ENABLE_EMAIL_NOTIFICATIONS = True
        
        mock_event = MagicMock(spec=JobExecutionEvent)
        mock_event.job_id = "test_failure_job_email"
        mock_event.exception = ValueError("Test Exception")
        mock_event.traceback = "Traceback here"
        
        # Chamar o listener diretamente com o evento mockado
        app.job_listener_error(mock_event)
        
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        self.assertIn("FALHA: Tarefa test_failure_job_email", args[0]) # Checar assunto
        self.assertIn("falhou durante a execução", args[1]) # Checar corpo
        self.assertIn("Test Exception", args[1])
        self.assertIn("Traceback here", args[1])

        # Restaurar para o valor original baseado no ambiente
        app.ENABLE_EMAIL_NOTIFICATIONS = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'False').lower() == 'true'

    @patch('app.send_email')
    def test_no_email_if_disabled_on_success(self, mock_send_email):
        app.ENABLE_EMAIL_NOTIFICATIONS = False # Explicitamente desabilitar
        
        mock_event = MagicMock(spec=JobExecutionEvent)
        mock_event.job_id = "test_success_job_no_email"
        mock_event.retval = "Success result"
        
        app.job_listener_success(mock_event)
        
        mock_send_email.assert_not_called()
        # Restaurar
        app.ENABLE_EMAIL_NOTIFICATIONS = os.getenv('ENABLE_EMAIL_NOTIFICATIONS', 'False').lower() == 'true'


    # Teste para verificar se a tarefa real é executada e o listener de sucesso é chamado
    # Este teste é um pouco mais complexo devido ao tempo.
    @patch('app.job_listener_success') # Mock o listener para verificar se é chamado
    def test_real_job_execution_success_triggers_listener(self, mock_job_listener_success):
        job_id = "real_job_run_success"
        
        # Agendar para rodar quase imediatamente.
        # Usar 'date' trigger para um tempo específico muito próximo ao presente.
        # No entanto, a execução real depende do scheduler estar rodando e do tempo do sistema.
        # Para testes unitários, é melhor mockar a execução da tarefa ou o listener.
        # Esta é uma tentativa de teste de integração mais leve.
        
        scheduler.add_job(
            func=example_task_success, # Usar a função diretamente
            id=job_id,
            trigger='date', 
            run_date=time.time() + 0.1 # Agendar para 0.1s no futuro
        )

        time.sleep(0.5) # Dar tempo para o scheduler processar e executar o job

        # Verificar se o listener foi chamado. O listener original (não o mockado) faria o log.
        # Aqui estamos verificando se nosso mock do listener foi chamado.
        # Precisamos garantir que o evento passado ao listener tenha o job_id correto.
        
        # Coletar todas as chamadas para o mock
        calls = mock_job_listener_success.call_args_list
        
        found_event_for_job = False
        for c in calls:
            event_arg = c.args[0] # O primeiro argumento posicional do listener é o evento
            if isinstance(event_arg, JobExecutionEvent) and event_arg.job_id == job_id:
                found_event_for_job = True
                break
        
        self.assertTrue(found_event_for_job, f"Listener de sucesso não foi chamado com o evento para job_id={job_id}")


if __name__ == '__main__':
    unittest.main()

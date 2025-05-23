# Agendador de Tarefas Python

## Descrição

Este projeto é um agendador de tarefas simples, construído em Python, que permite definir, agendar e monitorar tarefas (jobs). Ele oferece uma interface web básica para visualização das tarefas agendadas, persistência de jobs em um banco de dados SQLite e envia notificações por email sobre o status de execução das tarefas. Pode ser visto como uma alternativa muito leve e simplificada a ferramentas como o Airflow, focada em Python.

## Funcionalidades Principais

*   **Agendamento de Tarefas Python:** Permite agendar a execução de funções Python usando diferentes tipos de gatilhos (intervalo, data específica, cron).
*   **Interface Web:** Uma interface web simples (Flask) para visualizar as tarefas atualmente agendadas, seus IDs, nomes e próximos horários de execução.
*   **Monitoramento de Sucesso/Falha:** Loga a execução bem-sucedida ou falha das tarefas no console.
*   **Notificações por Email:** Envia emails automaticamente em caso de sucesso ou falha na execução de uma tarefa, se configurado.
*   **Persistência de Tarefas:** As tarefas agendadas são armazenadas em um banco de dados SQLite (`jobs.sqlite`), permitindo que o agendamento persista entre reinicializações da aplicação.

## Estrutura do Projeto

*   `app.py`: Contém a lógica principal da aplicação, incluindo a inicialização do scheduler APScheduler, a configuração do Flask para a interface web, e os listeners de eventos para monitoramento e notificações.
*   `tasks.py`: Arquivo destinado à definição das funções Python que serão agendadas como tarefas. Contém exemplos iniciais.
*   `email_notifications.py`: Módulo responsável pela lógica de envio de emails, utilizando `smtplib` e configurações de ambiente.
*   `requirements.txt`: Lista todas as dependências Python do projeto.
*   `.env.example`: Arquivo de exemplo para as variáveis de ambiente necessárias, principalmente para a configuração do serviço de email.
*   `jobs.sqlite`: Banco de dados SQLite onde o APScheduler armazena as informações das tarefas agendadas. É criado automaticamente na primeira execução.
*   `tests/`: Diretório contendo os testes automatizados do projeto.
    *   `tests/test_app.py`: Suíte de testes para a aplicação principal.
*   `.gitignore`: Especifica arquivos e diretórios que devem ser ignorados pelo Git (ex: `.env`, `__pycache__/`).
*   `README.md`: Este arquivo.

## Pré-requisitos

*   Python 3.8+
*   `pip` (gerenciador de pacotes Python, geralmente incluído com Python)

## Configuração (Setup)

1.  **Clone o repositório:**
    ```bash
    git clone <URL_DO_SEU_REPOSITORIO_AQUI> 
    # Substitua <URL_DO_SEU_REPOSITORIO_AQUI> pela URL real do seu repositório Git.
    cd nome-do-diretorio-do-projeto 
    # Navegue para o diretório do projeto clonado.
    ```

2.  **Crie e ative um ambiente virtual:**
    É altamente recomendado usar um ambiente virtual para isolar as dependências do projeto.
    ```bash
    python -m venv venv
    ```
    Para ativar o ambiente virtual:
    *   No Linux/macOS:
        ```bash
        source venv/bin/activate
        ```
    *   No Windows (cmd.exe):
        ```bash
        venv\Scripts\activate.bat
        ```
    *   No Windows (PowerShell):
        ```ps
        .\venv\Scripts\Activate.ps1
        ```

3.  **Instale as dependências:**
    Com o ambiente virtual ativado, instale as bibliotecas necessárias:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuração de Email (Opcional, mas recomendado):**
    Para receber notificações por email sobre o status das tarefas:
    *   Copie o arquivo de exemplo `.env.example` para um novo arquivo chamado `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Edite o arquivo `.env` com suas credenciais de servidor SMTP e endereços de email. Exemplo:
        ```env
        SMTP_HOST=smtp.example.com
        SMTP_PORT=587
        SMTP_USERNAME=seu_usuario_smtp
        SMTP_PASSWORD=sua_senha_smtp
        SENDER_EMAIL=remetente@example.com
        DEFAULT_RECEIVER_EMAIL=destinatario_padrao@example.com
        ENABLE_EMAIL_NOTIFICATIONS=True # Mude para False para desabilitar emails
        ```
    *   **Importante:** O arquivo `.env` contém informações sensíveis e já está incluído no `.gitignore` para evitar que seja enviado ao repositório Git. Certifique-se de que isso permaneça assim.

## Como Executar a Aplicação

1.  Certifique-se de que seu ambiente virtual está ativado e as dependências estão instaladas.
2.  Execute o script principal `app.py` a partir do diretório raiz do projeto:
    ```bash
    python app.py
    ```
3.  Após a inicialização, você verá logs no console indicando que o agendador e o servidor Flask foram iniciados.
    *   A interface web estará disponível em: `http://localhost:5000`
    *   As tarefas de exemplo (`example_task_success` e `example_task_failure` definidas em `tasks.py`) começarão a ser executadas nos intervalos configurados (a cada 10 e 15 segundos, respectivamente, por padrão).
    *   Logs de execução das tarefas serão exibidos no console.
    *   Se as notificações por email estiverem configuradas e habilitadas no arquivo `.env`, emails serão enviados para `DEFAULT_RECEIVER_EMAIL` informando o sucesso ou falha das tarefas.

## Como Executar os Testes

Para garantir que a aplicação está funcionando como esperado, você pode executar os testes automatizados.

1.  Certifique-se de que seu ambiente virtual está ativado.
2.  A partir do diretório raiz do projeto, execute:
    ```bash
    python -m unittest discover tests
    ```
    Este comando descobrirá e executará todos os testes no diretório `tests/`.

3.  Para executar um arquivo de teste específico (por exemplo, `tests/test_app.py`):
    ```bash
    python -m unittest tests.test_app
    ```

## Como Adicionar Novas Tarefas

1.  **Defina sua função Python:**
    Abra o arquivo `tasks.py` e defina a função que você deseja agendar. Por exemplo:
    ```python
    import logging

    logger = logging.getLogger(__name__) # Ou use logging.getLogger() para o logger raiz

    def minha_tarefa_personalizada(parametro1, parametro2="default"):
        logger.info(f"Executando minha_tarefa_personalizada com {parametro1} e {parametro2}...")
        # Coloque a lógica da sua tarefa aqui
        resultado = f"Resultado de {parametro1} + {parametro2}"
        logger.info("minha_tarefa_personalizada concluída com sucesso.")
        return resultado
    ```

2.  **Agende sua função em `app.py`:**
    Abra o arquivo `app.py`. Dentro do bloco `if __name__ == '__main__':` (ou em uma lógica de configuração mais avançada que você possa desenvolver), use a função `add_job_to_scheduler` para agendar sua nova tarefa.
    ```python
    if __name__ == '__main__':
        # ... (configuração e inicialização do scheduler e Flask) ...
        scheduler.start()
        logging.info("Agendador APScheduler iniciado.")

        # Agendamento das tarefas de exemplo existentes ...

        # Agendando sua nova tarefa
        add_job_to_scheduler(
            job_id="minha_tarefa_diaria_001",  # ID único para a tarefa
            func_path="tasks.minha_tarefa_personalizada",  # Caminho para a função
            trigger_args={
                'trigger': 'cron', 
                'hour': 3, 
                'minute': 0,
                # 'args': ['valor_param1', 'valor_param2_opcional'] # Para passar argumentos posicionais
                # 'kwargs': {'parametro1': 'valor_p1', 'parametro2': 'valor_p2'} # Para passar argumentos nomeados
            }
        )
        add_job_to_scheduler(
            job_id="outra_tarefa_intervalo",
            func_path="tasks.outra_funcao_simples", # Supondo que tasks.outra_funcao_simples exista
            trigger_args={'trigger': 'interval', 'minutes': 30}
        )

        # ... (restante do código para iniciar o Flask e o loop principal) ...
    ```
    *   **`job_id`**: Um identificador único para sua tarefa.
    *   **`func_path`**: O caminho completo para sua função, no formato `'nome_do_modulo.nome_da_funcao'`.
    *   **`trigger_args`**: Um dicionário especificando o tipo de gatilho e seus parâmetros. Exemplos:
        *   Intervalo: `{'trigger': 'interval', 'seconds': 30, 'minutes': 5, 'hours': 1, ...}`
        *   Data específica: `{'trigger': 'date', 'run_date': '2023-12-25 08:00:00'}`
        *   Cron: `{'trigger': 'cron', 'year': '*', 'month': '*', 'day': '*', 'week': '*', 'day_of_week': 'mon-fri', 'hour': 9, 'minute': 30, 'second': 0}` (veja a documentação do APScheduler para detalhes sobre cron).
        *   Para passar argumentos para sua função, adicione a chave `'args'` (para argumentos posicionais) ou `'kwargs'` (para argumentos nomeados) dentro de `trigger_args`.

## Contribuições

Contribuições são bem-vindas! Se você encontrar bugs, tiver sugestões de melhorias ou quiser adicionar novas funcionalidades, sinta-se à vontade para:

1.  Fazer um "fork" do repositório.
2.  Criar uma nova "branch" para suas modificações (`git checkout -b minha-feature`).
3.  Fazer "commit" de suas alterações (`git commit -am 'Adiciona nova feature'`).
4.  Fazer "push" para a "branch" (`git push origin minha-feature`).
5.  Abrir um "Pull Request".

Por favor, tente manter a consistência do código e adicione testes para novas funcionalidades, se aplicável.

---
*Este README foi gerado com base nas funcionalidades implementadas no projeto.*
```

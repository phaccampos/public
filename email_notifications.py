import smtplib
import os
import logging
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv() # Carrega variáveis do arquivo .env

# Configurações de Email (obtidas de variáveis de ambiente)
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587)) # Default para TLS
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
# DEFAULT_RECEIVER_EMAIL pode ser usado se 'to_email' não for especificado
DEFAULT_RECEIVER_EMAIL = os.getenv('DEFAULT_RECEIVER_EMAIL')


def send_email(subject: str, body: str, to_email: str = None):
    if not all([SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL]):
        logging.error("Configurações de SMTP incompletas. Email não pode ser enviado.")
        return False

    receiver = to_email if to_email else DEFAULT_RECEIVER_EMAIL
    if not receiver:
        logging.error("Destinatário do email não especificado e DEFAULT_RECEIVER_EMAIL não configurado.")
        return False

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver

    try:
        logging.info(f"Tentando enviar email para {receiver} com assunto: {subject}")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls() # Use TLS
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver, msg.as_string())
        logging.info(f"Email enviado com sucesso para {receiver}")
        return True
    except Exception as e:
        logging.error(f"Falha ao enviar email para {receiver}: {e}", exc_info=True)
        return False

if __name__ == '__main__':
    # Teste rápido de envio de email (requer .env configurado)
    logging.basicConfig(level=logging.INFO)
    if not DEFAULT_RECEIVER_EMAIL:
        print("Por favor, configure DEFAULT_RECEIVER_EMAIL no seu arquivo .env para testar.")
    else:
        if send_email("Teste de Email do Agendador", "Este é um email de teste.", DEFAULT_RECEIVER_EMAIL):
            print(f"Email de teste enviado para {DEFAULT_RECEIVER_EMAIL}, verifique a caixa de entrada.")
        else:
            print(f"Falha ao enviar email de teste. Verifique os logs e as configurações no .env.")

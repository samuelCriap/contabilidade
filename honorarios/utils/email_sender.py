"""
Módulo de envio de emails via Gmail SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

from database import get_config


def enviar_email(destinatario: str, assunto: str, corpo: str, anexo_path: str = None) -> tuple[bool, str]:
    """
    Envia um email via Gmail SMTP.
    
    Args:
        destinatario: Email do destinatário
        assunto: Assunto do email
        corpo: Corpo do email (texto)
        anexo_path: Caminho opcional para arquivo anexo (ex: PDF)
    
    Returns:
        Tuple (sucesso: bool, mensagem: str)
    """
    # Obter configurações
    email_remetente = get_config('empresa_email')
    senha_app = get_config('email_senha_app')
    nome_empresa = get_config('empresa_nome', 'Escritório Contábil')
    
    if not email_remetente:
        return False, "Email da empresa não configurado!"
    
    if not senha_app:
        return False, "Senha do App Gmail não configurada!"
    
    if not destinatario:
        return False, "Destinatário não informado!"
    
    try:
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = f"{nome_empresa} <{email_remetente}>"
        msg['To'] = destinatario
        msg['Subject'] = assunto
        
        # Corpo do email
        msg.attach(MIMEText(corpo, 'plain', 'utf-8'))
        
        # Anexo (se houver)
        if anexo_path and os.path.exists(anexo_path):
            with open(anexo_path, 'rb') as f:
                attachment = MIMEApplication(f.read(), _subtype='pdf')
                attachment.add_header(
                    'Content-Disposition', 
                    'attachment', 
                    filename=os.path.basename(anexo_path)
                )
                msg.attach(attachment)
        
        # Conectar ao SMTP do Gmail
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            # Remover espaços da senha (senhas do Google App vêm com espaços)
            senha_limpa = senha_app.replace(' ', '')
            server.login(email_remetente, senha_limpa)
            server.send_message(msg)
        
        return True, "Email enviado com sucesso!"
    
    except smtplib.SMTPAuthenticationError:
        return False, "Erro de autenticação. Verifique email e senha do app."
    except smtplib.SMTPException as e:
        return False, f"Erro SMTP: {str(e)}"
    except Exception as e:
        return False, f"Erro ao enviar email: {str(e)}"


def enviar_recibo_email(cliente_email: str, cliente_nome: str, recibo_path: str, 
                        mes: int, ano: int, valor: float) -> tuple[bool, str]:
    """
    Envia um recibo por email para o cliente.
    
    Args:
        cliente_email: Email do cliente
        cliente_nome: Nome do cliente
        recibo_path: Caminho do PDF do recibo
        mes: Mês de referência
        ano: Ano de referência
        valor: Valor do recibo
    
    Returns:
        Tuple (sucesso: bool, mensagem: str)
    """
    MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro", "13º Salário"]
    
    nome_empresa = get_config('empresa_nome', 'Escritório Contábil')
    mes_nome = MESES[mes - 1] if 1 <= mes <= 13 else str(mes)
    
    assunto = f"Recibo de Honorários - {mes_nome}/{ano}"
    
    valor_formatado = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    # Template padrão
    template_padrao = """Prezado(a) {cliente_nome},

Segue em anexo o recibo de honorários contábeis referente a {mes}/{ano}.

Valor: {valor}

Em caso de dúvidas, entre em contato conosco.

Atenciosamente,
{empresa_nome}"""
    
    # Usar template das configurações ou padrão
    template = get_config('email_template', template_padrao)
    
    # Substituir variáveis no template
    corpo = template.format(
        cliente_nome=cliente_nome,
        mes=mes_nome,
        ano=ano,
        valor=valor_formatado,
        empresa_nome=nome_empresa
    )
    
    return enviar_email(cliente_email, assunto, corpo, recibo_path)


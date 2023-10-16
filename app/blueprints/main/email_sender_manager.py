import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import dotenv_values

environ = dotenv_values(".env")

class EmailSenderManager:
    def __init__(self, 
                 username: str = None, 
                 password: str = None, 
                 use_tls: bool = None, 
                 use_ssl: bool = None) -> None:

        self.server_host = 'smtp.gmail.com'
        self.port = 465  # SSL port for Gmail
        self.use_tls = use_tls if use_tls is not None else False
        self.use_ssl = use_ssl if use_ssl is not None else True
        self.username = username or environ['MAIL_USERNAME']
        self.password = password or environ['MAIL_PASSWORD']

    def send_email(self, 
                   subject: str, 
                   sender: str, 
                   recipients: list, 
                   text_body: str, 
                   html_body: str) -> bool:

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)

        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")

        msg.attach(part1)
        msg.attach(part2)

        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.server_host, self.port) as server:
                    server.login(self.username, self.password)
                    server.sendmail(sender, recipients, msg.as_string())
            elif self.use_tls:
                with smtplib.SMTP(self.server_host, self.port) as server:
                    server.starttls()
                    server.login(self.username, self.password)
                    server.sendmail(sender, recipients, msg.as_string())
            else:
                with smtplib.SMTP(self.server_host, self.port) as server:
                    server.sendmail(sender, recipients, msg.as_string())
        except Exception as e:
            logging.error(e)
            return False

        return True

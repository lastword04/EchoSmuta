from typing import Protocol, Union
from typing_extensions import Self
from aiosmtplib import send
from email.message import EmailMessage
import logging
from ..schemas import EmailToSendSchema
from ....settings import SMTP

logger = logging.getLogger(__name__)

class EmailSenderServiceProtocol(Protocol):
    async def send_email(self: Self, email: EmailToSendSchema) -> Union[bool, str]:
        pass

class EmailSenderService(EmailSenderServiceProtocol):
    
    def __init__(self: Self, smtp: SMTP):
        self.smtp = smtp

    async def send_email(self: Self, email: EmailToSendSchema) -> Union[bool, str]:
        logger.info(f"Preparing to send email to {email.to_email}")
        message = EmailMessage()
        message["From"] = self.smtp.user
        message["To"] = email.to_email
        message["Subject"] = email.subject
        message.set_content("Ваш клиент не поддерживает HTML.")
        message.add_alternative(email.body, subtype="html")
        
        try:
            logger.info(f"Attempting to send email via SMTP to {self.smtp.host}:{self.smtp.port}")
            await send(
                message,
                hostname=self.smtp.host,
                port=self.smtp.port,
                username=self.smtp.user,
                password=self.smtp.password,
                start_tls=self.smtp.use_tls
            )
            logger.info(f"Successfully sent email to {email.to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {email.to_email}. Error: {str(e)}")
            return str(e) 

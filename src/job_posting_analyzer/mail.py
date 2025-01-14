import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(subject, body, recipient_address, sender_address, sender_password,
               **kwargs):
    message = MIMEMultipart()
    message["To"] = recipient_address
    message["From"] = sender_address
    message["Subject"] = subject

    message_text = MIMEText(body,'plain')
    message.attach(message_text)

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo('Gmail')
    server.starttls()
    server.login(sender_address, sender_password)
    fromaddr = sender_address
    toaddrs  = recipient_address
    server.sendmail(fromaddr,toaddrs,message.as_string())

    server.quit()
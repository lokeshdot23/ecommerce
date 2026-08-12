import smtplib
from email.message import EmailMessage


def send_mail(to, subject, body):
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login('mogalapallilokesh@gmail.com', 'kjyx dudn ztwe oayk')
            msg = EmailMessage()
            msg['FROM'] = 'mogalapallilokesh@gmail.com'
            msg['TO'] = to
            msg['SUBJECT'] = subject
            msg.set_content(body)
            server.send_message(msg)
    except Exception:
        print(Exception)
        print('email error')

# import smtplib
# from email.message import EmailMessage
# import requests
# from config import EMAIL_USER, EMAIL_PASSWORD


def notify(subject, body, method="console", recipient=None, webhook_url=None):
    if method == "console":
        print(f"[NOTIFICATION]\nSubject: {subject}\nMessage: {body}\n")

# def notify_email(subject, body, recipient=EMAIL_USER):
#     msg = EmailMessage()
#     msg.set_content(body)
#     msg['Subject'] = subject
#     msg['From'] = EMAIL_USER
#     msg['To'] = recipient
#     with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
#         server.login(EMAIL_USER, EMAIL_PASSWORD)
#         server.send_message(msg)

# def notify_slack(message, webhook_url):
#     payload = {"text": message}
#     requests.post(webhook_url, json=payload)
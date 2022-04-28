import smtplib, ssl

smtp_server = "smtp.gmail.com"
port = 587
sender_email = "crossroadsact@gmail.com"
password = input("password: ")

context = ssl.create_default_context()

def sendEmail(recipient_email, subject, body):
    server = smtplib.SMTP(smtp_server, port)
    server.ehlo()
    server.starttls(context=context)
    server.ehlo()
    server.login(sender_email, password)
    message = f"Subject: {subject}\n\n{body}"
    server.sendmail(sender_email, recipient_email, message)

    server.quit()
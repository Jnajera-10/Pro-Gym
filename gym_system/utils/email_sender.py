from flask_mail import Mail, Message
mail = Mail()

def send_email(app, to, subject, body):
    with app.app_context():
        msg = Message(subject, recipients=[to], body=body)
        mail.send(msg)

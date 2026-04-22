app_password='jvtt zysl jzjy ysvn'
import smtplib
from email.message import EmailMessage #class which is used to define  mail format 
def send_mail(to,subject,body): 
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('panayelanandini@gmail.com',app_password)
    msg=EmailMessage()
    msg['FROM']='panayelanandini@gmail.com'
    msg['SUBJECT']= subject
    msg['TO']= to
    msg.set_content(body)
    server.send_message(msg)
    server.close()
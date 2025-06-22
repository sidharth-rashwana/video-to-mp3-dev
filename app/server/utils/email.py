import smtplib
from fastapi import status
import os
import dns.resolver
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()
sender_email = os.getenv("SENDER_EMAIL")
sender_password= os.getenv("APP_PASSWORD")


def is_valid_email(email):
    try:
        # split email address to get domain name
        domain = email.split('@')[1]
        
        # get the MX record for the domain
        mx_records = []
        for mx in dns.resolver.query(domain, 'MX'):
            mx_records.append(mx.to_text().split()[1])
    
        # connect to the SMTP server of the domain and verify the email address
        smtp = smtplib.SMTP()
        smtp.connect(mx_records[0])
        smtp.verify(email)
        smtp.quit()
        
        return True
    except:
        return False

def send_email(receiver_email,content,subject):
    try:
        server=smtplib.SMTP('smtp.gmail.com',587)
        server.starttls()
        server.login(sender_email, sender_password)
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = receiver_email
        message['Subject'] = subject
        message.attach(content)
        
        response = server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        if not response:
            return {'status': status.HTTP_200_OK, 'message': 'Email sent successfully'}
        else:
            return {'status': status.HTTP_503_SERVICE_UNAVAILABLE, 'message': f'Failed to send email to {response}'}
    except smtplib.SMTPAuthenticationError:
        return {'status': status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': 'Authentication Error: Invalid email or password'}
    except smtplib.SMTPException as e:
        return {'status': status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': f'Error sending email: {str(e)}'}
    except Exception as e:
        return {'status': status.HTTP_500_INTERNAL_SERVER_ERROR, 'message': str(e)}
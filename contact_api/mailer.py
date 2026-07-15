import os, smtplib
from email.message import EmailMessage
FROM_EMAIL=os.environ.get('MAIL_FROM','hello@partylan.co.uk')
FROM_NAME=os.environ.get('MAIL_FROM_NAME','Party.LAN Website')
TO_EMAIL=os.environ.get('MAIL_TO','hello@partylan.co.uk')
def build_message(data):
    msg=EmailMessage(); msg['Subject']=f"Party.LAN enquiry: {data['intent']}"; msg['From']=f'{FROM_NAME} <{FROM_EMAIL}>'; msg['To']=TO_EMAIL; msg['Reply-To']=data['email']
    labels={'intent':'Enquiry type','name':'Name','email':'Email','phone':'Phone','package':'Package','preferred_date':'Preferred date','alternative_date':'Alternative date','location':'Town/postcode','players':'Players','message':'Message'}
    msg.set_content('\n'.join(f"{label}: {data.get(key) or '-'}" for key,label in labels.items()))
    return msg
def send_contact(data):
    msg=build_message(data)
    host=os.environ['SMTP_HOST']; port=int(os.environ.get('SMTP_PORT','587')); user=os.environ.get('SMTP_USERNAME'); password=os.environ.get('SMTP_PASSWORD')
    with smtplib.SMTP(host,port,timeout=10) as smtp:
        if os.environ.get('SMTP_STARTTLS','true').lower()=='true': smtp.starttls()
        if user and password: smtp.login(user,password)
        smtp.send_message(msg)

import re
from datetime import date
INTENTS={'availability','booking','question'}; PACKAGES={'onyx','jade','unsure'}
EMAIL_RE=re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
def clean(v): return str(v or '').strip()
def validate_contact(data):
    errors={}
    intent=clean(data.get('intent'))
    package=clean(data.get('package') or 'unsure')
    name=clean(data.get('name')); email=clean(data.get('email')); message=clean(data.get('message'))
    phone=clean(data.get('phone')); location=clean(data.get('location')); players=clean(data.get('players'))
    preferred=clean(data.get('preferred_date')); alt=clean(data.get('alternative_date'))
    if intent not in INTENTS: errors['intent']='Choose a supported enquiry type.'
    if package not in PACKAGES: errors['package']='Choose a supported package option.'
    if not 2 <= len(name) <= 80: errors['name']='Enter your name.'
    if not EMAIL_RE.match(email) or len(email)>120: errors['email']='Enter a valid email address.'
    if phone and not 7 <= len(phone) <= 30: errors['phone']='Enter a valid phone number, or leave it blank.'
    if location and not 2 <= len(location) <= 100: errors['location']='Enter a town or postcode, or leave it blank.'
    if players:
        try:
            n=int(players); assert 1 <= n <= 40
        except Exception: errors['players']='Enter a player count between 1 and 40.'
    for field,value in {'preferred_date':preferred,'alternative_date':alt}.items():
        if value:
            try: date.fromisoformat(value)
            except ValueError: errors[field]='Enter a valid date.'
    if message and not 10 <= len(message) <= 2000: errors['message']='Use 10 to 2000 characters.'
    if intent=='question' and not message: errors['message']='Enter a message.'
    if intent in {'availability','booking'}:
        if not message and not preferred: errors['preferred_date']='Add a preferred date or a message.'
        if not message and not location: errors['location']='Add a town/postcode or a message.'
    if data.get('privacy') not in (True,'true','on','1','yes'): errors['privacy']='Please acknowledge the privacy notice.'
    return errors, {'intent':intent,'package':package,'name':name,'email':email,'message':message,'phone':phone,'location':location,'players':players,'preferred_date':preferred,'alternative_date':alt}

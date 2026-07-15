from validation import validate_contact
def base(**kw):
    d={'intent':'question','name':'Alex','email':'alex@example.com','message':'Hello Party LAN','privacy':True,'package':'unsure'}; d.update(kw); return d
def test_question_requires_message():
    errors,_=validate_contact(base(message=''))
    assert 'message' in errors
def test_booking_allows_date_and_location_without_message():
    errors,_=validate_contact(base(intent='booking',message='',preferred_date='2026-08-01',location='Leeds'))
    assert errors=={}
def test_rejects_customer_from_style_invalid_email():
    errors,_=validate_contact(base(email='bad'))
    assert 'email' in errors

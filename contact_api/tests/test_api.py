import app as contact_app
def client(monkeypatch):
    monkeypatch.setattr(contact_app, 'send_contact', lambda data: None)
    contact_app.app.config['TESTING']=True
    return contact_app.app.test_client()
def test_health(monkeypatch):
    assert client(monkeypatch).get('/health').json == {'ok': True}
def test_rejects_non_json(monkeypatch):
    assert client(monkeypatch).post('/api/contact', data='x').status_code == 415
def test_accepts_valid_contact(monkeypatch):
    r=client(monkeypatch).post('/api/contact', json={'intent':'question','name':'Alex','email':'alex@example.com','message':'Hello Party LAN','privacy':True,'package':'unsure'})
    assert r.status_code == 200
    assert r.json['ok'] is True

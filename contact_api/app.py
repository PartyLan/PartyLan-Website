import os
from flask import Flask, jsonify, request
from validation import validate_contact
from rate_limit import MemoryRateLimiter
from mailer import send_contact
app=Flask(__name__); app.config['MAX_CONTENT_LENGTH']=32*1024
limiter=MemoryRateLimiter(int(os.environ.get('RATE_LIMIT_REQUESTS','5')), int(os.environ.get('RATE_LIMIT_WINDOW','600')))
@app.get('/health')
def health(): return jsonify(ok=True)
@app.post('/api/contact')
def contact():
    if not request.is_json: return jsonify(ok=False, message='Unsupported content type.'), 415
    if not limiter.allow(request.headers.get('X-Forwarded-For',request.remote_addr or 'unknown').split(',')[0].strip()): return jsonify(ok=False,message='Too many requests.'), 429
    data=request.get_json(silent=True)
    if not isinstance(data,dict): return jsonify(ok=False,message='Invalid JSON.'), 400
    errors, clean=validate_contact(data)
    if errors: return jsonify(ok=False,message='Please check your details.',errors=errors), 400
    try: send_contact(clean)
    except Exception: app.logger.exception('contact email failed'); return jsonify(ok=False,message='Service unavailable.'), 503
    return jsonify(ok=True,message='Your enquiry has been sent.')
@app.errorhandler(413)
def too_large(e): return jsonify(ok=False,message='Request too large.'), 413

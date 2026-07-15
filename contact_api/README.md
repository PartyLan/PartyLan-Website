# Party.LAN contact API

Small Flask service for `/api/contact`, deployed separately from the static site.

Email flow:

- From: `Party.LAN Website <hello@partylan.co.uk>`
- To: `hello@partylan.co.uk`
- Reply-To: the visitor email address

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r contact_api/requirements.txt
cd contact_api
flask --app app run
```

Configure SMTP with the variables in `.env.example`. Do not use the customer email as the From address.

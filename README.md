# JollyBee Beauty

A complete Python/Flask B2C beauty storefront with a responsive catalog, product search and category filters, session cart, customer accounts, order history, Stripe Checkout, signed Stripe webhooks, inventory updates, CSRF protection, secure password hashing, and production-ready configuration.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app run run --debug
```

Open `http://127.0.0.1:5000`. Products are seeded automatically on the first run.

## Stripe test payments

1. Create a Stripe account and copy a **test-mode** secret key into `.env` as `STRIPE_SECRET_KEY`.
2. Install the Stripe CLI and run:
   `stripe listen --forward-to localhost:5000/stripe/webhook`
3. Copy the reported `whsec_...` value into `.env` as `STRIPE_WEBHOOK_SECRET`, then restart Flask.
4. Use Stripe's test card `4242 4242 4242 4242`, any future date, and any CVC.

Card numbers are entered only on Stripe's hosted page and never pass through this application. The webhook signature is verified before an order is marked paid.

## Production checklist

- Set a random 32+ byte `SECRET_KEY`; never commit `.env`.
- Use PostgreSQL via `DATABASE_URL` and HTTPS so secure cookies are enabled.
- Register the production webhook URL in Stripe and use live keys only in the deployment secret manager.
- Replace demo contact links and product data, configure taxes/shipping in Stripe, and add transactional email.
- Run behind a reverse proxy with rate limiting, logging, monitoring, backups, and a Content Security Policy tailored to your image/font hosts.
- Review privacy, returns, accessibility, tax, and consumer-protection obligations for every market served.

## Tests

```bash
pip install pytest
pytest -q
```

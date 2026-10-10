# AI Pitch Deck Generator — Render Ready

Flask pitch-deck builder with PostgreSQL support, Anthropic Claude generation (when `ANTHROPIC_API_KEY` is configured), template fallback, PPTX export, PDF export, deck history, theme updates, and deck update/delete APIs.

## Deploy to Render
1. Push this folder's contents to a GitHub repository.
2. Create a Render Blueprint from `render.yaml`, or create a Python Web Service manually.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Set `ANTHROPIC_API_KEY` in Render Environment. Set `DATABASE_URL` to your Render PostgreSQL connection string and `FLASK_SECRET_KEY` to a long random secret.
6. Check `/health` after deploy.

Do not commit `.env` or real API keys. Claude requests fall back to the local template generator if the key is missing or the API request fails. Verify the model name available to your Anthropic account; override with `ANTHROPIC_MODEL` if needed.

## API additions
- `GET /health` and `GET /api/health`
- `POST /api/export-pdf`
- `PUT /api/decks/<id>` (update deck fields and/or slides)
- `DELETE /api/decks/<id>`

**Security note:** The existing app's data APIs are not yet protected by per-user authentication/authorization. Do not treat this build as a secure multi-user SaaS until authentication and ownership checks are implemented.


## Optional advanced planning calculations

The original interface and routes remain in place. An optional section adds an assumption-based planning slide when inputs are supplied. Formulas: contribution/customer = monthly price − variable cost; break-even customer count = ceiling(monthly operating costs ÷ positive contribution/customer); CAC = monthly marketing spend ÷ new paying customers; illustrative market capture = eligible target-market customer count × capture percentage. MRR/ARR are not presented as actual results without a paying-customer count. All outputs depend on the entered assumptions and are not verified forecasts.

\n## Google Login setup\n\n1. In Google Cloud Console, create an OAuth 2.0 Client ID (Web application) and configure the OAuth consent screen.\n2. Add your deployed Render URL to **Authorized JavaScript origins** (for example `https://YOUR-SERVICE.onrender.com`).\n3. Add `https://YOUR-SERVICE.onrender.com/auth/google/callback` to **Authorized redirect URIs**. For local testing, add `http://127.0.0.1:5000/auth/google/callback`.\n4. In Render → your web service → Environment, set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to the values from Google Cloud. Keep them private and do not commit them to GitHub.\n5. Redeploy. The home page will show the Google sign-in page; successful sign-in opens `/app`.\n\nGoogle sign-in requires valid OAuth credentials; it cannot complete until these Render environment variables and the redirect URI are configured.\n

## Render fixes included
- Adds the `requests` dependency required by Authlib's OAuth client.
- Explicitly configures Flask's `/static` directory and uses `url_for('static', ...)` for CSS and JavaScript URLs.
- Includes the Pitchora logo asset at `static/img/pitchora-logo.svg`.
- Declares `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` as Render Blueprint environment variables. Set both in Render before testing Google sign-in.

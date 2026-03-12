# URL Shortener Website with Ad Monetization

Production-style full-stack project with:
- **Frontend**: HTML + TailwindCSS + Vanilla JS
- **Backend**: Flask
- **Database**: MongoDB
- **Ad layer**: Monetag rewarded interstitial on redirect page

## Folder Structure

- `frontend/` static app (deploy to Vercel)
- `backend/` Flask API (deploy to Render)

## Local Development

### 1) Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export MONGO_URI='mongodb://localhost:27017/url_shortener'
export MONGO_DB_NAME='url_shortener'
export JWT_SECRET='replace-me'
export PUBLIC_BASE_URL='http://localhost:5000'
python app.py
```

### 2) Frontend

In another terminal:

```bash
cd frontend
python3 -m http.server 5173
```

Open `http://localhost:5173`.

> By default frontend points API requests to `http://localhost:5000` (`frontend/script.js`).

## API Endpoints

- `POST /api/signup`
- `POST /api/login`
- `POST /api/logout`
- `POST /api/shorten`
- `GET /r/<shortcode>`
- `GET /api/dashboard`
- `DELETE /api/link/<id>`
- `GET /api/admin/stats`

## Deploy Backend on Render

1. Push repo to GitHub.
2. Create a **Web Service** in Render.
3. Root directory: `backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app`
6. Add env vars:
   - `MONGO_URI`
   - `MONGO_DB_NAME=url_shortener`
   - `JWT_SECRET`
   - `PUBLIC_BASE_URL=https://<your-render-domain>`
   - `CORS_ORIGINS=https://<your-vercel-domain>`

## Deploy Frontend on Vercel

1. Import same repo in Vercel.
2. Set Root Directory to `frontend`.
3. Deploy as static site.
4. Update `frontend/script.js` `API_BASE` to your Render backend URL or set `window.API_BASE` via injected script.

## Monetag Integration

Monetag SDK is loaded in redirect template:

```html
<script src='//libtl.com/sdk.js' data-zone='10717096' data-sdk='show_10717096'></script>
```

Flow: when user opens `/r/<shortcode>`, backend logs click, serves ad page with 5-second countdown, then redirects to original URL after ad callback.

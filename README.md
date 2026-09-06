# FraudWatch — Credit Card Fraud Detection

A small full-stack demo:
- **Backend** (`/backend`): FastAPI + scikit-learn (RandomForest) trained on a
  synthetic transaction dataset, with JWT login protecting the API.
- **Frontend** (`/frontend`): plain HTML/CSS/JS — a login page and a
  fraud-risk dashboard. No build step, no framework.

```
frontend/
  index.html       login page
  dashboard.html   fraud detection console (protected)
  login.css / login.js
  dashboard.css / dashboard.js
  config.js        <- points the frontend at your backend URL
  images/

backend/
  main.py          FastAPI app + routes
  auth.py          login / JWT handling
  model.py         synthetic data + RandomForest training
  requirements.txt
  render.yaml
  .env.example
```

## How auth works

This ships with **one demo account** (no database) so the login page has
something real to check against:

- Username: `admin`
- Password: `12345`

Set your own via the `DEMO_USERNAME` / `DEMO_PASSWORD` environment variables.
`POST /api/auth/login` returns a JWT; the dashboard sends it as
`Authorization: Bearer <token>` on every API call. `/api/predict` and
`/api/model-info` reject requests without a valid token (401).
For real multi-user auth, swap `verify_credentials` in `backend/auth.py`
for a database lookup with hashed passwords.

## Run it locally

**Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # edit values if you want
uvicorn main:app --reload --port 8000
```
This trains the model on first startup (a few seconds) and serves the API at
`http://127.0.0.1:8000`.

**Frontend**
`config.js` already auto-detects `localhost` and points at
`http://127.0.0.1:8000`, so you just need to serve the static files:
```bash
cd frontend
python3 -m http.server 5500
```
Open `http://127.0.0.1:5500`, log in with `admin` / `12345`.

## Deploy the backend to Render

1. Push this project to a GitHub repo.
2. In Render: **New → Blueprint**, point it at your repo — it will pick up
   `backend/render.yaml` automatically and create the service.
   (Or **New → Web Service** manually: root directory `backend`,
   build command `pip install -r requirements.txt`,
   start command `uvicorn main:app --host 0.0.0.0 --port $PORT`.)
3. In the service's **Environment** tab, set:
   - `SECRET_KEY` — a long random string (Render's blueprint auto-generates one)
   - `DEMO_USERNAME`, `DEMO_PASSWORD` — your real demo login
   - `ALLOWED_ORIGINS` — leave as `*` for now, you'll fix this in step 5
4. Deploy. Note your backend URL, e.g. `https://fraud-detection-api.onrender.com`.
   Check it works: `https://fraud-detection-api.onrender.com/api/health`.

   Free-tier Render services sleep after inactivity — the first request after
   a while can take ~30–50s to wake up. That's normal.

## Deploy the frontend to Vercel

1. In `frontend/config.js`, set `PRODUCTION_API_BASE` to your Render URL:
   ```js
   const PRODUCTION_API_BASE = "https://fraud-detection-api.onrender.com";
   ```
2. In Vercel: **New Project**, import the repo, set the **root directory**
   to `frontend`. No framework/build step needed — leave build command empty
   and output directory as `frontend` (Vercel auto-detects a static site).
3. Deploy. Note your frontend URL, e.g. `https://fraudwatch.vercel.app`.

## Connect them (CORS)

Go back to Render → your backend service → **Environment**, and set:
```
ALLOWED_ORIGINS=https://fraudwatch.vercel.app
```
(comma-separate multiple origins if you have a preview URL too). Redeploy the
backend so the new CORS setting takes effect. Without this step the browser
will block the frontend's requests to the API with a CORS error.

Now open your Vercel URL, log in, and the dashboard will be calling your
live Render API.

## Notes

- The model is trained on **synthetic** data generated in `model.py` — it
  demonstrates the pipeline (features → RandomForest → probability →
  explanation), not real-world fraud patterns. Swap `generate_dataset()` for
  a loader over real labeled transaction data to make it production-relevant.
- Session tokens live in `sessionStorage`, so logging out or closing the tab
  clears them; they also expire server-side after `ACCESS_TOKEN_MINUTES`.

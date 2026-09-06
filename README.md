# FraudWatch — Credit Card Fraud Detection

FraudWatch is a simple full-stack web application that detects the **risk of credit card fraud** using Machine Learning.

It uses:

* **FastAPI** for the backend
* **Random Forest** for fraud detection
* **JWT** for login authentication
* **HTML, CSS, and JavaScript** for the frontend
* **Render** for backend deployment
* **Vercel** for frontend deployment

---
## Screenshot

## Interface

![image alt](https://github.com/Abeesh-2027/Credit-card-fraud-detection/blob/71218c78ace94df657db61a1c38c98eff91bf598/Screenshot%202026-09-06%20111322.png)

## Dashboard

![image alt](https://github.com/Abeesh-2027/Credit-card-fraud-detection/blob/dd846759505441debdfffe1a7d2608e33d7c2b74/Screenshot%202026-09-06%20111355.png)

---

## 📁 Project Structure

```text
FraudWatch/
│
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── model.py
│   ├── requirements.txt
│   ├── render.yaml
│   └── .env.example
│
└── frontend/
    ├── index.html
    ├── dashboard.html
    ├── login.css
    ├── login.js
    ├── dashboard.css
    ├── dashboard.js
    ├── config.js
    └── images/
```

---

## 🔐 Login

The application uses JWT authentication.

Default demo login:

```text
Username: admin
Password: 12345
```

You can change the username and password using environment variables:

```text
DEMO_USERNAME
DEMO_PASSWORD
```

After login, the server provides a JWT token.

The token is used to access protected API endpoints.

---

## 🤖 How Fraud Detection Works

The backend uses a **Random Forest Machine Learning model**.

The basic process is:

```text
Transaction Details
        ↓
Machine Learning Model
        ↓
Fraud Risk Prediction
        ↓
Risk Probability
        ↓
Dashboard Result
```

The model is currently trained using **synthetic data** generated inside `model.py`.

> This project is for demonstration and learning purposes. The synthetic dataset does not represent real-world fraud patterns.

---

# 🚀 Run Locally

## 1. Start the Backend

Open a terminal and run:

```bash
cd backend
pip install -r requirements.txt
```

Create your environment file:

```bash
cp .env.example .env
```

Then start the FastAPI server:

```bash
uvicorn main:app --reload --port 8000
```

The backend will run at:

```text
http://127.0.0.1:8000
```

You can also open the FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 2. Start the Frontend

Open another terminal:

```bash
cd frontend
python3 -m http.server 5500
```

Open:

```text
http://127.0.0.1:5500
```

Login using:

```text
Username: admin
Password: 12345
```

---

# ☁️ Deploy Backend to Render

### Step 1 — Push to GitHub

Push the project to your GitHub repository.

### Step 2 — Create Render Service

In Render:

```text
New → Web Service
```

Use:

```text
Root Directory: backend
```

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Important:** Use `0.0.0.0` and `$PORT` on Render.

### Step 3 — Add Environment Variables

Add:

```text
SECRET_KEY=your-secret-key
DEMO_USERNAME=admin
DEMO_PASSWORD=12345
ALLOWED_ORIGINS=*
```

After deployment, Render will give you a backend URL such as:

```text
https://your-backend-name.onrender.com
```

Test the backend:

```text
https://your-backend-name.onrender.com/api/health
```

---

# 🌐 Deploy Frontend to Vercel

Open:

```text
frontend/config.js
```

Change the production API URL:

```javascript
const PRODUCTION_API_BASE = "https://your-backend-name.onrender.com";
```

Then deploy the `frontend` folder to Vercel.

In Vercel:

```text
Root Directory: frontend
```

No framework or build command is required.

After deployment, you will get a URL similar to:

```text
https://fraudwatch.vercel.app
```

---

# 🔗 Connect Frontend and Backend

After getting your Vercel URL, go back to Render.

Change:

```text
ALLOWED_ORIGINS=*
```

to:

```text
ALLOWED_ORIGINS=https://fraudwatch.vercel.app
```

Then redeploy the backend.

Now the flow is:

```text
Vercel Frontend
       ↓
Render FastAPI Backend
       ↓
Random Forest Model
       ↓
Fraud Prediction
       ↓
Dashboard
```

---

# 🔒 Security

The project uses:

* JWT authentication
* Protected API endpoints
* Environment variables for secrets
* Session storage for login tokens
* CORS protection

The JWT token is stored in the browser's `sessionStorage`.

Logging out or closing the browser tab removes the session.

---

# ⚠️ Disclaimer

FraudWatch is an **educational/demo project**.

The Machine Learning model uses synthetic data and should **not** be used for real financial fraud detection without proper validation, real-world data, security testing, and production-level infrastructure.

---

## 🛠️ Technologies Used

| Technology    | Purpose                |
| ------------- | ---------------------- |
| Python        | Backend programming    |
| FastAPI       | REST API               |
| Scikit-learn  | Machine Learning       |
| Random Forest | Fraud prediction       |
| JWT           | Authentication         |
| HTML          | Frontend structure     |
| CSS           | Frontend design        |
| JavaScript    | Frontend functionality |
| Render        | Backend deployment     |
| Vercel        | Frontend deployment    |

---

## 👨‍💻 Project

**FraudWatch — Credit Card Fraud Detection**

A simple full-stack Machine Learning project demonstrating:

```text
Frontend + Backend + Authentication + Machine Learning + Deployment
```

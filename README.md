# RefundIQ+

A fraud-aware refund management system built with Flask. It analyzes refund requests using image analysis, video inspection, OCR invoice validation, and behavioral risk scoring to help businesses detect fraudulent claims.

## Features

- Customer portal to submit refund requests with photo/video/invoice evidence
- Automated fraud scoring (0–100) using computer vision and OCR
- Admin panel to review, approve, or reject refund requests
- JWT-based authentication with bcrypt password hashing
- Rate limiting on login and registration endpoints

## Tech Stack

- **Backend:** Flask, SQLAlchemy, Flask-JWT-Extended, Flask-Bcrypt, Flask-Limiter
- **Fraud Detection:** OpenCV, NumPy, Pytesseract (OCR)
- **Database:** SQLite (swappable via `DATABASE_URL`)

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/SonaBinu22/RefundIq.git
cd RefundIq
```

### 2. Create a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
copy .env.example .env   # Windows
cp .env.example .env     # Mac/Linux
```
Edit `.env` and set real values for `SECRET_KEY` and `JWT_SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Run
```bash
python app.py
```

Open `http://127.0.0.1:5000`

## Default Admin Account

On first run a default admin is created. **Change the password immediately.**

| Field    | Value                  |
|----------|------------------------|
| Email    | admin@refundiq.com     |
| Password | admin123               |

Change password via `POST /api/change-password` with a valid JWT token.

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/register` | — | Register a new customer |
| POST | `/api/login` | — | Login and get JWT token |
| GET | `/api/me` | JWT | Get current user info |
| POST | `/api/change-password` | JWT | Change password |
| POST | `/api/submit-refund` | JWT | Submit a refund request |
| GET | `/api/my-refunds` | JWT | List own refund requests |
| GET | `/api/refund/<id>` | JWT | Get a specific refund |
| GET | `/api/admin/refunds` | Admin JWT | List all refunds |
| POST | `/api/admin/refund/<id>/decision` | Admin JWT | Approve or reject |
| GET | `/api/admin/users` | Admin JWT | List all users |

# RefundIQ+

A fraud-aware refund management system built with Flask. It analyzes refund requests using image analysis, video inspection, OCR invoice validation, and behavioral risk scoring to help businesses detect fraudulent claims.

## Features

- Customer portal to submit refund requests with photo/video/invoice evidence
- Automated fraud scoring (0–100) using computer vision and OCR
- Admin panel to review, approve, or reject refund requests
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





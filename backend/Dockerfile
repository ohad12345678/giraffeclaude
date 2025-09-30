FROM python:3.11-slim

WORKDIR /app

# העתקת requirements
COPY requirements.txt .

# התקנת תלויות
RUN pip install --no-cache-dir -r requirements.txt

# העתקת קוד האפליקציה
COPY . .

# הגדרת PORT
ENV PORT=8080

# הרצת האפליקציה עם gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app
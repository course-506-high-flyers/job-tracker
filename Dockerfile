FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn
RUN pip install --no-cache-dir gunicorn

# Copy the rest of the app
COPY . .

EXPOSE 8000

# Run under gunicorn, not flask run
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]

FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "-m", "flask", "--app", "app.py", "run", "--host=0.0.0.0", "--port=5000"]

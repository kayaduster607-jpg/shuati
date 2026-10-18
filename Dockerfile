FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask flask-cors

COPY app.py .

RUN mkdir -p /data /app/static

EXPOSE 4000

CMD ["python", "app.py"]

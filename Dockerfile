FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends tzdata cron && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY .env.example ./
ENV FLASK_APP=app.main:app
RUN useradd -m appuser
USER appuser
EXPOSE 8080
CMD ["python","-m","app.run"]

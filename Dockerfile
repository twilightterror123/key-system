FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server ./server
COPY bot ./bot
COPY client ./client

ENV DATABASE_PATH=/data/licenses.db
EXPOSE 9821

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "9821"]

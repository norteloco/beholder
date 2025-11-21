FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .

RUN python -m venv .venv && \
    source .venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["/app/.venv/bin/python", "./app.py"]
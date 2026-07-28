# Foundry hosted agent — Capital Markets research assistant
# x86_64, serves on port 8088 per the hosted-agent container contract.
# Build for linux/amd64 (pass --platform linux/amd64 to `az acr build`/`docker build`).
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8088

CMD ["python", "app.py"]

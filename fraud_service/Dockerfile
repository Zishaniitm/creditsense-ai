# fraud_service/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY fraud_service/requirements.txt fraud_service/requirements.txt
RUN pip install --no-cache-dir -r fraud_service/requirements.txt

COPY ml/models/ ml/models/
COPY fraud_service/ fraud_service/

EXPOSE 5001
CMD ["python", "fraud_service/app.py"]
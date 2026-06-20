# ml_service/Dockerfile
# Build context MUST be the project root: docker compose handles this automatically.
FROM python:3.12-slim

WORKDIR /app

# Install only what this service needs at inference time (not training/SHAP-plotting deps)
COPY ml_service/requirements.txt ml_service/requirements.txt
RUN pip install --no-cache-dir -r ml_service/requirements.txt

# Trained model artifacts — copied explicitly, not the whole ml/ folder,
# to keep the image lean (training scripts, raw data, etc. are not needed at runtime)
COPY ml/models/ ml/models/
COPY ml/evaluation/shap_feature_importance.json ml/evaluation/shap_feature_importance.json

COPY ml_service/ ml_service/

EXPOSE 5000
CMD ["python", "ml_service/app.py"]
# One image: builds the React app, then serves it and the API with uvicorn.
FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /srv
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend backend
# retrain so the saved models match the scikit-learn version in this image
RUN python backend/ml/train.py
COPY --from=web /web/dist frontend/dist
ENV COOKIE_SECURE=1
EXPOSE 8000
WORKDIR /srv/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Build the React frontend first
FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json ./
COPY frontend/ ./
RUN npm install && npm run build

# Build the Python backend
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend /frontend/dist ./frontend/dist

EXPOSE 8000
CMD ["python", "main.py"]

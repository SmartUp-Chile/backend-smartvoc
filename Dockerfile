FROM python:3.9-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_DEBUG=1

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar requisitos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install watchdog

# Para hot reload
EXPOSE 5000

# No copiamos el código aquí para permitir hot reload con volúmenes
# El código se montará como volumen

# Usar gunicorn para producción o Flask para desarrollo
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"] 
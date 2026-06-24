FROM python:3.12-slim

WORKDIR /app

# System deps for pdfplumber's underlying pdfminer (none heavy needed,
# but keep build tools minimal and remove after install)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as non-root user
RUN useradd -m appuser && mkdir -p /app/instance && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# 2 workers is plenty for a small internal team tool; increase if needed.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "app:create_app()"]

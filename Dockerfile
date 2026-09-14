FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY rag_pipeline.py .
COPY vector_database.py .
COPY report_service.py .
COPY api_server.py .
COPY agents/ agents/
COPY api/ api/

# Install Python dependencies
RUN pip install --no-cache-dir .

# Create directories for runtime data
RUN mkdir -p pdfs vectorstore

EXPOSE 8000

CMD ["python", "api_server.py"]

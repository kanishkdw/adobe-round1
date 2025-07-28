FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

# Install system dependencies for PDF processing and ML libraries
RUN apt-get update && apt-get install -y \
    poppler-utils \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY round_1b/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Copy source code
COPY round_1b/src/ ./src/
COPY shared/ ./shared/

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Set Python path to include shared directory
ENV PYTHONPATH=/app

CMD ["python", "src/main.py"] 
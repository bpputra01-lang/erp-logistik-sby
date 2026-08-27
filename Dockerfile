FROM python:3.12-slim

# Install system dependencies (curl, nodejs, unzip)
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs

# Set working directory
WORKDIR /app

# Copy project files
COPY erp-reflex-sby/ /app/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir reflex reflex-hosting-cli && \
    if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Initialize Reflex and compile frontend
RUN reflex init
RUN reflex export --frontend-only --no-zip

# Hugging Face default port is 7860
EXPOSE 7860

# Run reflex production mode on port 7860
CMD ["reflex", "run", "--env", "prod", "--frontend-port", "7860", "--backend-port", "8000"]

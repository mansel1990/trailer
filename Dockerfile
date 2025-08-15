# Use a lightweight Python base image
FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Install build essentials for some packages (like numpy, scipy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch (CPU-only) and other dependencies
# Use a specific index URL for torch+cpu to avoid CUDA binaries
COPY requirements.txt .
RUN pip install --no-cache-dir \
    -f https://download.pytorch.org/whl/cpu/torch_stable.html \
    -r requirements.txt

# Pre-download the SentenceTransformer model during build
# This avoids large downloads during runtime/startup on Railway
ENV SENTENCE_TRANSFORMERS_HOME=/app/models
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy your application code
COPY . .

# Ensure the virtual environment's bin directory is in PATH
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port (Railway will set $PORT env var)
EXPOSE 8000

# Command to run the application
# This is usually overridden by Railway's Procfile, but good to have as fallback
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 
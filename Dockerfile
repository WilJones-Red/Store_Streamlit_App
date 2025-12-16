# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port for Streamlit
EXPOSE 8080

# Set environment variable for port (Cloud Run compatibility)
ENV PORT=8080

# Run Streamlit app with dynamic port support
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true

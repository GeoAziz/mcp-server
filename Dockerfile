# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port 8000
EXPOSE 8000

# Run the server with uvicorn
CMD ["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY api_gateway/ .

# Expose port
EXPOSE 5000

# Run the service
CMD ["python", "app.py"]



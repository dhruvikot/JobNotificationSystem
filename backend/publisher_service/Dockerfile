FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY publisher_service/ .

# Copy shared libraries
COPY libs /app/libs

# Expose port
EXPOSE 5003

# Run the service
CMD ["python", "app.py"]



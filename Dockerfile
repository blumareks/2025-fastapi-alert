# Base image (must match OpenShift's S2I Python builder, or a compatible one)
FROM python:3.12-slim

# Install OS dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /opt/app

# Copy source code and requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Use uvicorn as the ASGI server
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8080", "main:app"]

# Base image (must match OpenShift's S2I Python builder, or a compatible one)
FROM python:3.11-slim

# Required for S2I to detect this as a Python app
LABEL io.openshift.s2i.build.source-location="."

# Install OS dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    APP_MODULE=main:app \
    GOOGLE_API_KEY=your-default-api-key-if-any

# Create application directory
WORKDIR /opt/app

# Copy source code and requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Use uvicorn as the ASGI server
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8080","main:app"]

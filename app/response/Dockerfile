FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the response engine code
COPY . .

# Run the Incident Responder
CMD ["python", "incident_response.py"]
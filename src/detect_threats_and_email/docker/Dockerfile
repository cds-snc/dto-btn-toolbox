# Use a specific, slim version of Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /usr/src/app

# Copy requirements first to leverage Docker cache
COPY src/detect_threats_and_email/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/detect_threats_and_email/ .

# Copy config files
COPY config/config.ini /usr/config/config.ini
COPY config/cacert-2023-01-10.pem /usr/config/cacert-2023-01-10.pem

# Expose port
EXPOSE 80

# Command to run the application
CMD ["python", "./pft_detect_threats_and_email.py"]

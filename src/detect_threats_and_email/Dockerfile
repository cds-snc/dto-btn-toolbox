FROM python:3.9

WORKDIR /usr/src/app

# Copy the application code
COPY src/detect_threats_and_email/ .

# Copy config files
COPY config/config.ini /usr/config/config.ini
COPY config/cacert-2023-01-10.pem /usr/config/cacert-2023-01-10.pem

# Install packages
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

CMD ["python", "./PFT_detect_threats_and_email.py"]

#!/bin/sh

# Set GPG_TTY to the current tty
export GPG_TTY=$(tty)

# Decrypt config.ini.gpg
gpg --quiet --batch --yes --decrypt --passphrase="$APPLICATION_SECRETS_PASSPHRASE" \
    --output ./config/config.ini ./config/config.ini.gpg

# Decrypt cacert-2023-01-10.pem.gpg
gpg --quiet --batch --yes --decrypt --passphrase="$APPLICATION_SECRETS_PASSPHRASE" \
    --output ./config/cacert-2023-01-10.pem ./config/cacert-2023-01-10.pem.gpg

gpg --quiet --batch --yes --decrypt --passphrase="$APPLICATION_SECRETS_PASSPHRASE" \
    --output ./config/tier1_2_spreadsheets_credentials.json ./config/tier1_2_spreadsheets_credentials.json.gpg

# List contents of the config directory
ls -la ./config

#!/bin/sh

# Set GPG_TTY to the current tty
export GPG_TTY=$(tty)


# Decrypt config.ini
gpg --quiet --batch --yes --decrypt --passphrase="$SECRET_PASSPHRASE" \
    --output ./config/config.ini config/config.ini.gpg

# Decrypt cacert-2023-01-10.pem
gpg --quiet --batch --yes --decrypt --passphrase="$SECRET_PASSPHRASE" \
    --output ./config/cacert-2023-01-10.pem config/cacert-2023-01-10.pem.gpg

# List contents of the config directory
ls -la ./config

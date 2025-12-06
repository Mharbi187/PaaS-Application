#!/bin/bash

##############################################################################
# Framework Installation Script
# Automatically installs dependencies for various frameworks
##############################################################################

set -e  # Exit on error

FRAMEWORK=$1

if [ -z "$FRAMEWORK" ]; then
    echo "Error: Framework not specified"
    echo "Usage: $0 <framework>"
    exit 1
fi

echo "========================================="
echo "Installing framework: $FRAMEWORK"
echo "========================================="

# Update system
echo "Updating system packages..."
apt-get update -y
apt-get upgrade -y

# Install common dependencies
echo "Installing common dependencies..."
apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release

# Framework-specific installation
case "$FRAMEWORK" in
    django|flask|fastapi)
        echo "Installing Python environment..."
        apt-get install -y \
            python3 \
            python3-pip \
            python3-venv \
            python3-dev
        
        # Install framework-specific packages
        if [ "$FRAMEWORK" == "django" ]; then
            pip3 install django gunicorn psycopg2-binary
        elif [ "$FRAMEWORK" == "flask" ]; then
            pip3 install flask gunicorn
        elif [ "$FRAMEWORK" == "fastapi" ]; then
            pip3 install fastapi uvicorn[standard]
        fi
        ;;
    
    laravel)
        echo "Installing PHP and Laravel environment..."
        
        # Add PHP repository
        add-apt-repository -y ppa:ondrej/php
        apt-get update -y
        
        # Install PHP and extensions
        apt-get install -y \
            php8.2 \
            php8.2-cli \
            php8.2-fpm \
            php8.2-mysql \
            php8.2-pgsql \
            php8.2-sqlite3 \
            php8.2-redis \
            php8.2-memcached \
            php8.2-json \
            php8.2-mbstring \
            php8.2-xml \
            php8.2-curl \
            php8.2-zip \
            php8.2-bcmath \
            php8.2-intl \
            php8.2-gd \
            nginx
        
        # Install Composer
        curl -sS https://getcomposer.org/installer | php
        mv composer.phar /usr/local/bin/composer
        chmod +x /usr/local/bin/composer
        ;;
    
    express|react|vuejs|nextjs)
        echo "Installing Node.js environment..."
        
        # Install Node.js 18.x
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt-get install -y nodejs
        
        # Install yarn (optional)
        npm install -g yarn
        
        # Install PM2 for process management
        npm install -g pm2
        ;;
    
    *)
        echo "Warning: Unknown framework '$FRAMEWORK'. Installing basic tools only."
        ;;
esac

# Install Nginx as reverse proxy (if not already installed)
if ! command -v nginx &> /dev/null; then
    echo "Installing Nginx..."
    apt-get install -y nginx
fi

# Install supervisor for process management
echo "Installing Supervisor..."
apt-get install -y supervisor

# Create application directory
echo "Creating application directory..."
mkdir -p /opt/app
chown -R $USER:$USER /opt/app

# Configure firewall (if ufw is available)
if command -v ufw &> /dev/null; then
    echo "Configuring firewall..."
    ufw --force enable
    ufw allow ssh
    ufw allow http
    ufw allow https
    # Allow application ports
    ufw allow 3000/tcp  # Node.js / React
    ufw allow 5000/tcp  # Flask
    ufw allow 8000/tcp  # Django / Laravel / FastAPI
fi

echo "========================================="
echo "Framework installation completed!"
echo "Framework: $FRAMEWORK"
echo "========================================="

exit 0

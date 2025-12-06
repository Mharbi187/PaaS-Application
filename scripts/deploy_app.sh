#!/bin/bash

##############################################################################
# Application Deployment Script
# Clones GitHub repository and deploys the application
##############################################################################

set -e  # Exit on error

GITHUB_URL=$1
FRAMEWORK=$2

if [ -z "$GITHUB_URL" ] || [ -z "$FRAMEWORK" ]; then
    echo "Error: Missing required arguments"
    echo "Usage: $0 <github_url> <framework>"
    exit 1
fi

echo "========================================="
echo "Deploying application"
echo "GitHub: $GITHUB_URL"
echo "Framework: $FRAMEWORK"
echo "========================================="

# Application directory
APP_DIR="/opt/app"
cd $APP_DIR

# Clone repository
echo "Cloning repository..."
if [ -d ".git" ]; then
    echo "Repository already exists, pulling latest changes..."
    git pull origin main || git pull origin master
else
    git clone $GITHUB_URL .
fi

# Framework-specific deployment
case "$FRAMEWORK" in
    django)
        echo "Deploying Django application..."
        
        # Create virtual environment
        python3 -m venv venv
        source venv/bin/activate
        
        # Install dependencies
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
        fi
        
        # Run migrations
        if [ -f "manage.py" ]; then
            python manage.py migrate --noinput || true
            python manage.py collectstatic --noinput || true
        fi
        
        # Create Gunicorn configuration
        cat > gunicorn_config.py <<EOF
bind = "0.0.0.0:8000"
workers = 3
worker_class = "sync"
timeout = 120
EOF
        
        # Create supervisor configuration
        cat > /etc/supervisor/conf.d/django-app.conf <<EOF
[program:django-app]
directory=$APP_DIR
command=$APP_DIR/venv/bin/gunicorn -c gunicorn_config.py wsgi:application
autostart=true
autorestart=true
stderr_logfile=/var/log/django-app.err.log
stdout_logfile=/var/log/django-app.out.log
EOF
        
        supervisorctl reread
        supervisorctl update
        supervisorctl start django-app
        ;;
    
    flask)
        echo "Deploying Flask application..."
        
        # Create virtual environment
        python3 -m venv venv
        source venv/bin/activate
        
        # Install dependencies
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
        fi
        
        # Create Gunicorn configuration
        cat > gunicorn_config.py <<EOF
bind = "0.0.0.0:5000"
workers = 3
worker_class = "sync"
timeout = 120
EOF
        
        # Create supervisor configuration
        cat > /etc/supervisor/conf.d/flask-app.conf <<EOF
[program:flask-app]
directory=$APP_DIR
command=$APP_DIR/venv/bin/gunicorn -c gunicorn_config.py app:app
autostart=true
autorestart=true
stderr_logfile=/var/log/flask-app.err.log
stdout_logfile=/var/log/flask-app.out.log
EOF
        
        supervisorctl reread
        supervisorctl update
        supervisorctl start flask-app
        ;;
    
    fastapi)
        echo "Deploying FastAPI application..."
        
        # Create virtual environment
        python3 -m venv venv
        source venv/bin/activate
        
        # Install dependencies
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
        fi
        
        # Create supervisor configuration
        cat > /etc/supervisor/conf.d/fastapi-app.conf <<EOF
[program:fastapi-app]
directory=$APP_DIR
command=$APP_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
autostart=true
autorestart=true
stderr_logfile=/var/log/fastapi-app.err.log
stdout_logfile=/var/log/fastapi-app.out.log
EOF
        
        supervisorctl reread
        supervisorctl update
        supervisorctl start fastapi-app
        ;;
    
    laravel)
        echo "Deploying Laravel application..."
        
        # Install dependencies
        composer install --no-dev --optimize-autoloader
        
        # Set permissions
        chown -R www-data:www-data $APP_DIR
        chmod -R 755 $APP_DIR
        chmod -R 775 $APP_DIR/storage $APP_DIR/bootstrap/cache
        
        # Copy .env file if it doesn't exist
        if [ ! -f ".env" ] && [ -f ".env.example" ]; then
            cp .env.example .env
            php artisan key:generate
        fi
        
        # Run migrations
        php artisan migrate --force || true
        
        # Optimize
        php artisan config:cache
        php artisan route:cache
        php artisan view:cache
        
        # Configure Nginx
        cat > /etc/nginx/sites-available/laravel-app <<EOF
server {
    listen 8000;
    root $APP_DIR/public;
    index index.php index.html;
    
    location / {
        try_files \$uri \$uri/ /index.php?\$query_string;
    }
    
    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.2-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME \$realpath_root\$fastcgi_script_name;
        include fastcgi_params;
    }
}
EOF
        
        ln -sf /etc/nginx/sites-available/laravel-app /etc/nginx/sites-enabled/
        nginx -t && systemctl reload nginx
        ;;
    
    express)
        echo "Deploying Express.js application..."
        
        # Install dependencies
        if [ -f "package.json" ]; then
            npm install --production
        fi
        
        # Start with PM2
        pm2 delete express-app || true
        pm2 start index.js --name express-app
        pm2 save
        pm2 startup
        ;;
    
    react|vuejs|nextjs)
        echo "Deploying $FRAMEWORK application..."
        
        # Install dependencies
        if [ -f "package.json" ]; then
            npm install
        fi
        
        # Build application
        npm run build || true
        
        # Serve with PM2 (for Next.js) or Nginx (for React/Vue)
        if [ "$FRAMEWORK" == "nextjs" ]; then
            pm2 delete nextjs-app || true
            pm2 start npm --name nextjs-app -- start
            pm2 save
        else
            # Configure Nginx to serve static files
            BUILD_DIR="build"
            [ "$FRAMEWORK" == "vuejs" ] && BUILD_DIR="dist"
            
            cat > /etc/nginx/sites-available/frontend-app <<EOF
server {
    listen 3000;
    root $APP_DIR/$BUILD_DIR;
    index index.html;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
            
            ln -sf /etc/nginx/sites-available/frontend-app /etc/nginx/sites-enabled/
            nginx -t && systemctl reload nginx
        fi
        ;;
    
    *)
        echo "Warning: Unknown framework '$FRAMEWORK'. No deployment steps executed."
        exit 1
        ;;
esac

echo "========================================="
echo "Application deployed successfully!"
echo "Framework: $FRAMEWORK"
echo "========================================="

exit 0

# PaaS Application - Quick Start Guide

## 🚀 Quick Launch

### Windows
Simply double-click `start_paas.bat` or run:
```bash
start_paas.bat
```

### Manual Launch
```bash
# Activate virtual environment
.venv\Scripts\activate

# Run application
python app.py
```

## ✅ Pre-Launch Health Check

Run the health check script before starting:
```bash
python health_check.py
```

This will validate:
- ✅ .env configuration
- ✅ Required directories
- ✅ Python dependencies
- ✅ Terraform binary

## 🔧 Common Issues & Solutions

### Issue 1: Missing .env file
**Error:** `.env file not found`

**Solution:**
```bash
# Copy example file
copy .env.example .env

# Edit .env with your settings
notepad .env
```

### Issue 2: Module not found
**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
```bash
# Install dependencies
.venv\Scripts\pip install -r requirements.txt
```

### Issue 3: Port already in use
**Error:** `Address already in use`

**Solution:**
```bash
# Stop existing Python processes
taskkill /F /IM python.exe

# Or change port in .env
APP_PORT=5001
```

### Issue 4: Database errors
**Error:** `OperationalError: no such table`

**Solution:**
```bash
# Delete database and restart (it will recreate)
del instance\paas.db
python app.py
```

### Issue 5: Terraform not found
**Error:** `Terraform binary not found`

**Solution:**
- Ensure `terraform_bin/terraform.exe` exists
- Or download from: https://www.terraform.io/downloads.html

### Issue 6: SSH key errors
**Error:** `SSH key not found` or `Permission denied`

**Solution:**
```bash
# Keys will be auto-generated on first deployment
# Or manually create ssh_keys directory
mkdir ssh_keys
```

### Issue 7: Proxmox connection failed
**Error:** `Connection refused` or `Authentication failed`

**Solution:**
1. Check `.env` settings:
   ```
   PROXMOX_URL=https://YOUR_IP:8006/api2/json
   PROXMOX_USER=terraform@pve
   PROXMOX_PASSWORD=your_password
   ```
2. Test Proxmox connection:
   ```bash
   curl -k https://YOUR_IP:8006/api2/json/version
   ```

## 📋 Environment Variables Reference

Required variables in `.env`:

```bash
# Proxmox Configuration
PROXMOX_URL=https://192.168.100.2:8006/api2/json
PROXMOX_USER=terraform@pve
PROXMOX_PASSWORD=your_password
PROXMOX_NODE=proxmox
PROXMOX_STORAGE=local-lvm

# Application Settings
APP_HOST=0.0.0.0
APP_PORT=5000
DEBUG=True
SECRET_KEY=change-this-in-production

# Network Configuration
GATEWAY=192.168.100.1
DNS_SERVERS=8.8.8.8,8.8.4.4

# SSH Configuration (optional)
SSH_USER=root
```

## 🔐 Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Never commit `.env` file
- [ ] Never commit `ssh_keys/` directory
- [ ] Use strong Proxmox passwords
- [ ] Enable SSL in production
- [ ] Disable DEBUG in production

## 📊 Accessing the Application

Once started, access:
- **Local:** http://127.0.0.1:5000
- **Network:** http://YOUR_IP:5000

Dashboard endpoints:
- `/` - Home page
- `/dashboard` - Deployments dashboard
- `/deploy` - New deployment form
- `/api/stats` - Statistics API
- `/health` - Health check

## 🛠️ Maintenance

### View Logs
```bash
# Real-time logs
Get-Content logs\paas.log -Wait -Tail 50

# Or open in notepad
notepad logs\paas.log
```

### Clean Up Deployments
```bash
# Destroy specific deployment
cd terraform
..\terraform_bin\terraform.exe workspace select <deployment_name>
..\terraform_bin\terraform.exe destroy -auto-approve
```

### Reset Everything
```bash
# Stop application
taskkill /F /IM python.exe

# Clean databases
del instance\paas.db

# Clean Terraform states
rmdir /S /Q terraform\states

# Clean logs
del logs\*.log

# Restart
python app.py
```

## 🐛 Debug Mode

Enable detailed logging:
```bash
# In .env
DEBUG=True
LOG_LEVEL=DEBUG
```

## 📞 Support

If issues persist:
1. Check `logs\paas.log` for detailed errors
2. Run health check: `python health_check.py`
3. Verify Proxmox connectivity
4. Check GitHub repo: https://github.com/Mharbi187/PaaS-Application

## 🎯 Success Indicators

Application is working correctly when you see:
```
✅ Logging initialized
✅ Running on http://127.0.0.1:5000
✅ Running on http://192.168.0.X:5000
```

Test deployment:
1. Open http://127.0.0.1:5000
2. Click "New Deployment"
3. Enter GitHub URL: https://github.com/Mharbi187/FrontEnd
4. Select LXC + React
5. Click Deploy
6. Watch the logs for success!

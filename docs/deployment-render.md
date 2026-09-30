# Deploying Report-OIML on Render

This guide explains how to deploy the Report-OIML application on Render.

## Quick Deploy Option

### Option 1: Using render.yaml (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `Pawan-webdeveloper/Report-OIML`
4. Render will automatically detect the `render.yaml` file
5. Click **"Apply"** to use the configuration
6. Click **"Create Web Service"**

### Option 2: Manual Configuration

If you prefer to configure manually:

1. **Create New Web Service**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click **"New +"** → **"Web Service"**
   - Connect your GitHub account and select `Pawan-webdeveloper/Report-OIML`

2. **Basic Settings**
   - **Name**: `Report-OIML` (or your preferred name)
   - **Region**: Choose closest to you (e.g., Oregon)
   - **Branch**: `feat/backend-setup`
   - **Root Directory**: `backend` ⚠️ **IMPORTANT**
   - **Environment**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt && cd ../frontend && npm ci && npm run build:backend
     ```
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

3. **Environment Variables**
   Add these environment variables:
   - `DATABASE_URL` = `sqlite:///./data.db`
   - `SECRET_KEY` = (generate a random secure string)
   - `ALLOW_ANY_LOGIN` = `true`
   - `UPLOAD_DIR` = `./uploads`
   - `PYTHON_VERSION` = `3.12.0`

4. **Add Persistent Disk** (for file uploads)
   - Click **"Advanced"** → **"Add Disk"**
   - **Name**: `uploads`
   - **Mount Path**: `/opt/render/project/src/backend/uploads`
   - **Size**: 1 GB

5. **Deploy**
   - Click **"Create Web Service"**
   - Wait for the build to complete (5-10 minutes)

## Common Issues & Solutions

### Issue 1: "Could not open requirements file"

**Problem**: 
```
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'
```

**Solution**: 
Set **Root Directory** to `backend` in Render settings. This tells Render to run commands from the `backend/` directory where `requirements.txt` is located.

### Issue 2: WeasyPrint not working

**Problem**: PDF export fails with library errors.

**Solution**: 
Render's Python environment includes the necessary system libraries. If issues persist, add this to your build command:
```bash
pip install -r requirements.txt && apt-get update && apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

### Issue 3: Frontend build fails

**Problem**: `npm ci` or `npm run build:backend` fails.

**Solution**: 
Ensure Node.js is available. Add to environment variables:
- `NODE_VERSION` = `20.0.0`

### Issue 4: Database errors

**Problem**: Database connection fails.

**Solution**: 
- For SQLite: Ensure `DATABASE_URL=sqlite:///./data.db`
- For PostgreSQL: Use Render's managed database and update `DATABASE_URL` accordingly

## Using PostgreSQL (Production Recommended)

For production deployments, use PostgreSQL instead of SQLite:

1. **Create PostgreSQL Database**
   - In Render Dashboard, click **"New +"** → **"PostgreSQL"**
   - Name: `report-oiml-db`
   - Copy the **Internal Database URL**

2. **Update Environment Variables**
   - Set `DATABASE_URL` to the Internal Database URL
   - Format: `postgresql://user:password@host:port/dbname`

3. **Run Migrations**
   Add to build command:
   ```bash
   pip install -r requirements.txt && alembic upgrade head && cd ../frontend && npm ci && npm run build:backend
   ```

## Post-Deployment

### Initial Setup

1. **Access your application**
   - URL will be: `https://report-oiml.onrender.com` (or your chosen name)

2. **Login with default credentials**
   ```
   Username: admin
   Password: admin123
   ```

3. **Change default password immediately!**
   - Go to Profile → Change Password

### Monitoring

- View logs in Render Dashboard → "Logs" tab
- Monitor resource usage in "Metrics" tab
- Set up alerts for errors

### Updating the Application

When you push changes to GitHub:
1. Render automatically detects changes
2. New build is triggered
3. Application redeploys with latest changes

To manually trigger a deploy:
- Go to "Manual Deploy" → **"Deploy latest commit"**

## Performance Optimization

### Free Tier Limitations

- **Spin down**: Service sleeps after 15 minutes of inactivity
- **Wake up time**: ~30-60 seconds on next request
- **Monthly hours**: 750 hours (shared across all services)

### Optimization Tips

1. **Use keep-alive pings** to prevent spin-down:
   - Use a service like [UptimeRobot](https://uptimerobot.com/) to ping your endpoint every 5 minutes

2. **Optimize database queries**
   - Use connection pooling
   - Add indexes for frequently queried fields

3. **Cache static assets**
   - Frontend build includes caching headers
   - Consider using a CDN for static files

## Security Checklist

- [ ] Change default admin password
- [ ] Set strong `SECRET_KEY` (use: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] Set `ALLOW_ANY_LOGIN=false` for production
- [ ] Enable HTTPS (automatic on Render)
- [ ] Configure CORS properly in `backend/app/core/config.py`
- [ ] Set `COOKIE_SECURE=true` for HTTPS
- [ ] Regular database backups
- [ ] Monitor logs for suspicious activity

## Troubleshooting

### Build Fails

1. Check build logs in Render Dashboard
2. Verify all environment variables are set
3. Ensure `requirements.txt` and `package.json` are valid
4. Try building locally first:
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ../frontend
   npm ci
   npm run build:backend
   ```

### Application Crashes

1. Check runtime logs
2. Verify environment variables
3. Check database connectivity
4. Ensure disk is mounted correctly for uploads

### Can't Access Application

1. Verify service is running (not suspended)
2. Check URL is correct
3. Verify port configuration (`$PORT` environment variable)
4. Check firewall/security group settings

## Support

- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com/)
- [Render Status](https://status.render.com/)

## Cost Estimation

**Free Tier**:
- 750 hours/month
- 512 MB RAM
- 0.1 CPU
- Suitable for development/demo

**Starter Plan ($7/month)**:
- Always on (no spin-down)
- 512 MB RAM
- 0.5 CPU
- Suitable for small production

**Standard Plan ($25/month)**:
- Always on
- 2 GB RAM
- 1 CPU
- Suitable for production with moderate traffic

---

**Need help?** Check the main [README.md](../README.md) or open an issue on GitHub.

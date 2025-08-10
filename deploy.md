# 🚀 Render Deployment Guide

## Quick Deploy (Free Tier)

1. **Push to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy to Render**:
   - Go to [render.com](https://render.com) and sign up/login
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`
   - Click "Apply" to deploy both services

3. **Access Your Deployed App**:
   - API: `https://iris-ml-api.onrender.com`
   - Frontend: `https://iris-ml-frontend.onrender.com`

## ✅ Fixed Issues in render.yaml:

- **Removed invalid configurations** (disk mounts not available on free tier)
- **Simplified environment variables** (removed redundant envVarGroups)
- **Fixed static site type** (was incorrectly set as web service)
- **Added mkdir command** to ensure artifacts directory exists
- **Removed PORT override** (Render manages this automatically)

## What Gets Deployed

✅ **FastAPI ML Service** (Free Web Service)
- All API endpoints: `/predict`, `/health`, `/metrics`, `/retrain`
- Automatic model training during build
- Health checks and monitoring

✅ **Static Frontend** (Free Static Site)
- Interactive web dashboard
- Real-time predictions
- System monitoring

## Free Tier Limitations

- **Cold starts**: ~30 seconds after inactivity
- **Build time**: ~10 minutes for ML dependencies
- **Memory**: 512MB RAM
- **Storage**: 1GB persistent disk
- **Bandwidth**: 100GB/month

## Production Considerations

For production use, consider upgrading to:
- **Starter Plan** ($7/month): Faster builds, no cold starts
- **PostgreSQL**: For production logging (free tier available)
- **Redis**: For model caching (free tier available)

## Environment Variables

The deployment automatically sets:
- `PORT`: Render-assigned port
- `MODEL_PATH`: Path to trained model
- `ENVIRONMENT`: Set to "production"

## Monitoring

- Health checks: `/health` endpoint
- Metrics: `/metrics` endpoint (Prometheus format)
- Logs: Available in Render dashboard

## Cost: $0/month on Free Tier! 💰
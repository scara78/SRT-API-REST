# Deployment Guide

This OpenSubtitles REST API can be deployed on multiple platforms. Choose the option that works best for you.

## 🚀 Vercel Deployment (Recommended)

### Prerequisites
- [Vercel account](https://vercel.com) (free tier available)
- [Vercel CLI](https://vercel.com/cli) installed: `npm i -g vercel`

### Quick Deploy Steps

1. **Clone or download this project**
2. **Install Vercel CLI and login**:
   ```bash
   npm i -g vercel
   vercel login
   ```

3. **Deploy to Vercel**:
   ```bash
   vercel
   ```

4. **Set up environment variables** in Vercel dashboard:
   - Go to your project settings on vercel.com
   - Add these environment variables:
     - `OPENSUBTITLES_USERNAME` = your username
     - `OPENSUBTITLES_PASSWORD` = your password
     - `SESSION_SECRET` = any random string (e.g., "your-secret-key-123")

5. **Done!** Your API will be available at `https://your-project.vercel.app`

### Vercel Environment Variables Setup

After deployment, configure these secrets in your Vercel dashboard:

```
OPENSUBTITLES_USERNAME=scara78
OPENSUBTITLES_PASSWORD=scara78
SESSION_SECRET=your-random-secret-key
```

## 🛠️ Replit Deployment

Your app is already running on Replit! To deploy:

1. Click the **Deploy** button in your Replit workspace
2. Follow the deployment wizard
3. Your app will be available at a `.replit.app` domain

## 📝 API Endpoints

Once deployed, your API will have these endpoints:

- `GET /api/v1/status` - API health check
- `GET /api/v1/search` - Search subtitles
- `GET /api/v1/download/{file_id}` - Get download links
- `POST /api/v1/convert` - Convert subtitle formats
- `GET /api/v1/demo` - Sample responses

## 🔗 Testing Your Deployment

After deployment, test your API:

```bash
# Check status
curl https://your-domain.com/api/v1/status

# Search subtitles
curl "https://your-domain.com/api/v1/search?imdb_id=tt0120338&languages=en"
```

## 🔧 Configuration

The app automatically detects your OpenSubtitles credentials and shows the authentication status at `/api/v1/status`.

For web players, use the `/api/v1/search` endpoint to get direct subtitle file links.
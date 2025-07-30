#!/bin/bash

# Vercel Deployment Script for OpenSubtitles API
echo "🚀 Deploying OpenSubtitles REST API to Vercel..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

echo "📋 Make sure you have your OpenSubtitles.org credentials ready:"
echo "   - Username: OPENSUBTITLES_USERNAME" 
echo "   - Password: OPENSUBTITLES_PASSWORD"
echo ""

# Deploy to Vercel
echo "🔄 Starting deployment..."
vercel --prod

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Go to your Vercel dashboard: https://vercel.com/dashboard"
echo "2. Find your project and click on it"
echo "3. Go to Settings > Environment Variables"
echo "4. Add these variables:"
echo "   OPENSUBTITLES_USERNAME = scara78"
echo "   OPENSUBTITLES_PASSWORD = scara78"
echo "   SESSION_SECRET = your-random-secret-key"
echo ""
echo "🔗 Test your API at: https://your-project.vercel.app/api/v1/status"
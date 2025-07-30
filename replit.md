# OpenSubtitles REST API

## Overview

This is a Flask-based REST API that provides subtitle search and format conversion services using the OpenSubtitles.org XML-RPC API. The application serves as a proxy service that simplifies subtitle retrieval and offers automatic format conversion between SRT and VTT formats, making it ideal for web player integration.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular Flask architecture with separation of concerns:

### Backend Architecture
- **Framework**: Flask with CORS enabled for cross-origin requests
- **API Design**: RESTful API with versioned endpoints (`/api/v1/`)
- **Service Layer**: Modular services for subtitle operations, format conversion, and caching
- **Static Assets**: Frontend interface for API testing and documentation

### Key Design Principles
- **Modular Services**: Each major functionality is encapsulated in its own service class
- **Rate Limiting**: Built-in protection against API abuse with configurable intervals
- **Caching**: In-memory caching with TTL to reduce external API calls
- **Error Handling**: Comprehensive error handling and logging throughout the application

## Key Components

### Core Services

1. **SubtitleService** (`subtitle_service.py`)
   - Interfaces with OpenSubtitles.org XML-RPC API
   - Handles authentication with session tokens
   - Implements rate limiting to respect API quotas
   - Supports multiple search methods (IMDB ID, text query, file hash)
   - Direct subtitle content download and decoding

2. **FormatConverter** (`format_converter.py`)
   - Converts between SRT and VTT subtitle formats
   - Handles both content conversion and URL-based conversion
   - Uses regex patterns for format transformation

3. **CacheManager** (`cache_manager.py`)
   - In-memory caching with TTL (Time To Live) support
   - Automatic cleanup of expired entries
   - Hash-based key management for consistent caching

### API Endpoints

- **GET /api/v1/search**: Main search endpoint supporting multiple parameters
  - `imdb_id`: Search by IMDB movie ID
  - `query`: Text-based search
  - `moviehash`: File hash-based search
  - `languages`: Language filtering
  - `format`: Output format preference (SRT/VTT)

### Frontend Interface
- **Testing Interface**: HTML/JavaScript interface for API testing
- **Documentation**: Embedded API documentation with examples
- **Responsive Design**: Bootstrap-based UI with dark theme

## Data Flow

1. **Request Processing**: Client sends search request with parameters
2. **Cache Check**: System checks for cached results first
3. **API Integration**: If not cached, queries OpenSubtitles.com API
4. **Authentication**: Manages JWT tokens for API access
5. **Format Conversion**: Converts subtitles to requested format if needed
6. **Response Caching**: Caches successful responses for future requests
7. **Response Delivery**: Returns formatted subtitle data to client

## External Dependencies

### Required Services
- **OpenSubtitles.org API**: Primary subtitle data source
  - Requires username and password (no API key needed)
  - Session token-based authentication
  - Rate-limited access (1 request per second minimum)
  - XML-RPC protocol for communication

### Python Dependencies
- **Flask**: Web framework and routing
- **Flask-CORS**: Cross-origin request support
- **requests**: HTTP client for external API calls

### Environment Variables
- `OPENSUBTITLES_USERNAME`: Account username for OpenSubtitles.org
- `OPENSUBTITLES_PASSWORD`: Account password for OpenSubtitles.org
- `SESSION_SECRET`: Flask session security key

## Deployment Strategy

### Development Setup
- **Entry Point**: `main.py` runs the Flask development server
- **Configuration**: Environment-based configuration
- **Logging**: Debug-level logging enabled
- **CORS**: Enabled for all routes to support frontend testing

### Production Considerations
- **Rate Limiting**: Built-in rate limiting prevents API quota exhaustion
- **Error Handling**: Comprehensive error responses with appropriate HTTP status codes
- **Caching**: In-memory cache reduces external API dependencies
- **Security**: API key and credential management through environment variables

### Scalability Notes
- **Stateless Design**: Application is stateless except for in-memory cache
- **Cache Strategy**: Current in-memory cache could be replaced with Redis for distributed deployments
- **Rate Limiting**: Per-instance rate limiting may need coordination in multi-instance deployments

The application is designed to be a lightweight, efficient proxy for subtitle services with built-in optimizations for web player integration and API quota management.

## Recent Implementation Status (July 30, 2025)

### 🔄 Major Migration Completed
**OpenSubtitles.com → OpenSubtitles.org Migration**
- Successfully migrated from REST API (.com) to XML-RPC API (.org)
- Simplified authentication: username/password only (no API key required)
- Improved performance with direct subtitle content access
- Updated all deployment configurations and documentation

### ✅ Completed Features
- **OpenSubtitles.org XML-RPC Integration** - Successfully migrated from .com to .org API with session authentication
- **JSON API Endpoints** - All endpoints return valid JSON responses as required
- **Format Conversion** - SRT to VTT and VTT to SRT conversion working perfectly
- **Rate Limiting & Caching** - Implemented to respect API quotas and improve performance
- **Web Interface** - Complete testing interface with Bootstrap dark theme
- **Error Handling** - Comprehensive error responses in JSON format
- **Authentication Status** - API properly detects and reports credential configuration
- **Direct Download Links** - Successfully generating direct links to decompressed SRT/VTT content (not .gz files)
- **Content Serving** - New endpoint serves raw subtitle text with proper headers for web players

### 🔧 Technical Verification
- **API Status**: All endpoints operational and returning valid JSON
- **OpenSubtitles.org Integration**: Successfully connecting with XML-RPC, authenticating, and downloading subtitles
- **Format Support**: Both SRT and VTT formats fully supported with conversion
- **Cache Performance**: In-memory caching working with TTL support
- **Rate Limiting**: 1-second minimum intervals implemented to respect API limits
- **Session Management**: Proper login/logout cycle with token management
- **Credentials**: Authenticated with scara78 account on OpenSubtitles.org
- **Real Data**: Successfully retrieving and processing actual subtitle files
- **Content Decompression**: Automatically downloads .gz files and serves plain text SRT/VTT
- **Web Player Ready**: Direct links serve subtitle content with proper CORS and content headers
- **Docker Support**: Complete containerization with Docker Compose and Portainer management

### 🚀 Deployment Options
- **Docker** - Containerized deployment with Docker Compose and Portainer support
- **Vercel** - Serverless deployment with `vercel.json` configuration and deployment script
- **Replit** - Direct deployment from workspace with built-in hosting
- **Self-hosted** - Standard Flask application compatible with any WSGI server

### 📁 Deployment Files
- **Docker**: `Dockerfile`, `docker-compose.yml`, `docker-compose.portainer.yml`, `DOCKER.md`
- **Vercel**: `vercel.json`, `deploy-vercel.sh` - Serverless deployment configuration
- **General**: `DEPLOY.md` - Complete deployment guide for all platforms
# EzCut Frontend

A modern React TypeScript frontend for the EzCut video processing application. This frontend connects to the FastAPI backend to provide a seamless video processing experience.

## Features

- 🎥 **Video Upload**: Drag & drop multiple video files
- 🔄 **Real-time Processing**: Live updates during video processing
- 📊 **Processing History**: View and manage processed videos
- 🎯 **Narrative Generation**: AI-powered video narrative creation
- 🌐 **API Integration**: Full integration with FastAPI backend
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- EzCut Backend API running (see backend setup below)

### Installation

1. **Install dependencies:**
   ```bash
   cd ezcut/client
   npm install
   ```

2. **Configure API endpoint (optional):**
   ```bash
   # Create .env file in client directory
   echo "VITE_API_BASE_URL=http://localhost:8000" > .env
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## Backend Setup

The frontend requires the EzCut FastAPI backend to be running. Here's how to set it up:

### Start the Backend API

1. **Navigate to the project root:**
   ```bash
   cd ezcut
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the FastAPI server:**
   ```bash
   cd api
   python main.py
   ```

   The API will be available at `http://localhost:8000`

### Verify Backend Connection

- The frontend will show a connection status indicator in the header
- Green checkmark = Backend connected ✅
- Red warning = Backend offline ❌
- You can also test the API directly: `curl http://localhost:8000/health`

## Architecture

### API Integration

The frontend connects to these backend endpoints:

- `POST /upload-videos` - Upload and process videos
- `GET /job/{job_id}` - Get processing status
- `GET /jobs` - List all jobs
- `DELETE /job/{job_id}` - Delete a job
- `GET /health` - Health check

### Real-time Updates

Processing status is updated in real-time using polling:

1. Upload videos → Get job ID
2. Poll job status every 2 seconds
3. Update UI with progress and messages
4. Complete when narrative is generated

### Components

- `CurrentItem.tsx` - Main video processing interface
- `HistoryTab.tsx` - Job history management
- `ConnectionStatus.tsx` - API connection indicator
- `api/client.ts` - API client with polling utilities

## Configuration

### Environment Variables

Create a `.env` file in the client directory:

```bash
# API Backend URL
VITE_API_BASE_URL=http://localhost:8000

# Optional: Enable API request logging
VITE_DEBUG_API=true
```

### Customization

The API base URL can be configured in several ways:

1. **Environment variable** (recommended):
   ```bash
   VITE_API_BASE_URL=http://your-backend-url:8000
   ```

2. **Direct modification** in `src/api/client.ts`:
   ```typescript
   const API_BASE_URL = 'http://your-backend-url:8000';
   ```

## Usage Guide

### Processing Videos

1. **Upload**: Drag & drop video files or click to select
2. **Preview**: Click on uploaded files to preview
3. **Process**: Click "Process Videos" to start AI processing
4. **Monitor**: Watch real-time progress updates
5. **Review**: Edit the generated narrative script
6. **Export**: Download or further process results

### Managing History

- View all processed jobs in the History tab
- Filter by status (completed, processing, failed)
- Search by title or filename
- Delete individual jobs or clear all
- Retry failed jobs

## Development

### Available Scripts

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint

# Type checking
npm run type-check
```

### Tech Stack

- **React 19** with TypeScript
- **Vite** for fast development and building
- **TailwindCSS** for styling
- **Axios** for API communication
- **React Dropzone** for file uploads
- **Lucide React** for icons

### API Client

The `api/client.ts` module provides:

- Typed API functions
- Request/response interceptors
- Error handling
- Job status polling utilities
- Connection health monitoring

## Troubleshooting

### Common Issues

1. **"Backend offline" error:**
   - Ensure the FastAPI server is running on port 8000
   - Check if `http://localhost:8000/health` responds
   - Verify no firewall blocking the connection

2. **CORS errors:**
   - The backend includes CORS middleware for all origins
   - Check browser console for specific CORS issues

3. **File upload fails:**
   - Check file format (supports MP4, MOV, AVI, MKV, WebM, TS)
   - Verify backend has sufficient disk space
   - Check network connection for large files

4. **Processing gets stuck:**
   - Check backend logs for processing errors
   - Ensure video_processor.py dependencies are installed
   - Verify NLP model availability

### Debug Mode

Enable debug logging by setting:

```bash
VITE_DEBUG_API=true
```

This will log all API requests and responses to the browser console.

## Production Deployment

### Build for Production

```bash
npm run build
```

The `dist/` folder contains the production build ready for deployment.

### Environment Configuration

For production, set the API URL:

```bash
VITE_API_BASE_URL=https://your-production-api.com
```

### Deployment Options

- **Static hosting**: Netlify, Vercel, GitHub Pages
- **Container**: Docker with nginx
- **CDN**: AWS CloudFront, Cloudflare

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with the backend API
5. Submit a pull request

## License

This project is part of the EzCut video processing suite.

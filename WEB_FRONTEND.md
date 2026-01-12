# Web Frontend Guide

## Overview

The web frontend allows you to view and manage your job search pipeline from any device on your network. This is especially useful when running the pipeline on a Jetson Nano and viewing results on your PC.

## Features

- **Dashboard**: View statistics and overview of your job search
- **Job Browser**: Filter and search through saved jobs
- **Unextracted Jobs**: Monitor jobs that failed extraction
- **Resume Management**: View and download generated resumes
- **Real-time Updates**: Auto-refreshes every 30 seconds

## Running the Web Server

### On Jetson Nano (or any server)

```bash
# Run on all interfaces (accessible from other devices)
python web_app.py --host 0.0.0.0 --port 5000

# Or run on a specific port
python web_app.py --host 0.0.0.0 --port 8080
```

### On Local Machine (development)

```bash
# Run locally only
python web_app.py --host 127.0.0.1 --port 5000
```

## Accessing from PC

1. **Find the Jetson Nano IP address:**
   ```bash
   # On Jetson Nano
   hostname -I
   ```

2. **Open in browser:**
   ```
   http://<jetson-ip>:5000
   ```
   
   Example: `http://192.168.1.100:5000`

## API Endpoints

The web app provides a REST API:

- `GET /api/stats` - Get database statistics
- `GET /api/jobs` - Get jobs with filters
- `GET /api/jobs/<id>` - Get specific job
- `POST /api/jobs/<id>/mark-applied` - Mark job as applied
- `GET /api/unextracted` - Get unextracted jobs
- `GET /api/resumes` - Get generated resumes
- `GET /api/resumes/<id>/pdf` - Download resume PDF
- `POST /api/search/run` - Run a job search

## Security Note

The web server is designed for local network use. For production or internet-facing deployments, add authentication and HTTPS.

## Troubleshooting

### Can't access from PC

1. Check firewall settings on Jetson Nano
2. Verify Jetson Nano IP address
3. Ensure `--host 0.0.0.0` is used (not `127.0.0.1`)
4. Check that the port is not blocked

### Port already in use

```bash
# Use a different port
python web_app.py --port 8080
```

### PDF downloads not working

Ensure PDFs are generated (check `data/resumes/` directory) and that the file paths in the database are correct.

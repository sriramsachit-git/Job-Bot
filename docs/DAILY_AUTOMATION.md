# 🤖 Automated Daily Job Search

This document explains how to set up the job search pipeline to run automatically every day at 9 AM.

## Quick Start

### Run Once Now
```bash
python daily_runner.py
```

This will:
1. Search for new jobs
2. Extract and parse job postings
3. Generate resumes for top matches
4. Start the web server
5. Open your browser to view results

### Run as Daemon (Continuous)
```bash
python daily_runner.py --daemon
```

This will:
1. Start the web server immediately
2. Run the job search at 9 AM every day
3. Keep running until you stop it

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--daemon` / `-d` | Run as daemon with scheduled execution | Off |
| `--schedule` / `-s` | Schedule time (HH:MM format) | `09:00` |
| `--no-web` | Don't start web server | Web starts |
| `--no-browser` | Don't open browser automatically | Opens browser |
| `--port` / `-p` | Web server port | `5000` |
| `--no-resume` | Don't generate resumes automatically | Generates |
| `--top-jobs` / `-t` | Number of top jobs for resume generation | `5` |
| `--min-score` / `-m` | Minimum relevance score | `30` |

## Examples

```bash
# Run at 8:30 AM
python daily_runner.py --daemon --schedule "08:30"

# Run without web server (for background processing)
python daily_runner.py --no-web

# Generate resumes for top 10 jobs
python daily_runner.py --top-jobs 10

# Run on a different port
python daily_runner.py --port 8080
```

## Automated Scheduling

### Option 1: Cron (Linux/Mac) - Recommended

Run the setup script:
```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

Or manually add to crontab:
```bash
crontab -e
```

Add this line:
```
0 9 * * * cd /path/to/job_search_pipeline && python3 daily_runner.py --run-once >> logs/daily_runner.log 2>&1
```

### Option 2: Systemd Service (Linux) - For Daemon Mode

Run the setup script:
```bash
sudo ./setup_systemd.sh
```

Or manually:
```bash
# Copy service file
sudo cp job-search.service /etc/systemd/system/

# Edit paths in the service file
sudo nano /etc/systemd/system/job-search.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable job-search
sudo systemctl start job-search
```

### Option 3: Windows Task Scheduler

Run as Administrator:
```cmd
setup_windows_task.bat
```

Or manually:
1. Open Task Scheduler (`taskschd.msc`)
2. Create Basic Task → "DailyJobSearch"
3. Trigger: Daily at 9:00 AM
4. Action: Start Program
   - Program: `python`
   - Arguments: `C:\path\to\daily_runner.py --run-once`
   - Start in: `C:\path\to\job_search_pipeline`

### Option 4: Jetson Nano Setup

For running on Jetson Nano with PC access:

```bash
# On Jetson Nano
python daily_runner.py --daemon --host 0.0.0.0 --port 5000

# Access from PC
# Open browser: http://<jetson-ip>:5000
```

Find Jetson IP:
```bash
hostname -I
```

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAILY AUTOMATED FLOW                          │
└─────────────────────────────────────────────────────────────────┘

          ┌──────────────┐
          │  9:00 AM     │
          │  Trigger     │
          └──────┬───────┘
                 │
                 ▼
┌────────────────────────────────┐
│  Phase 1: Job Search           │
│  ─────────────────────────     │
│  1. Google Search API          │
│  2. Extract content            │
│  3. Parse with GPT-4o-mini     │
│  4. Score & filter             │
│  5. Save to database           │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│  Phase 2: Resume Generation    │
│  ─────────────────────────     │
│  1. Rank projects for top jobs │
│  2. Auto-select top 3 projects │
│  3. Generate LaTeX resumes     │
│  4. Compile to PDF             │
└────────────────┬───────────────┘
                 │
                 ▼
┌────────────────────────────────┐
│  Phase 3: Web Dashboard        │
│  ─────────────────────────     │
│  1. Start Flask server         │
│  2. Open browser               │
│  3. View jobs & resumes        │
└────────────────────────────────┘
```

## Monitoring

### Check Logs

**Cron logs:**
```bash
cat logs/daily_runner.log
```

**Systemd logs:**
```bash
sudo journalctl -u job-search -f
```

### Web Dashboard

Access the dashboard to see:
- Total jobs found
- New jobs saved
- Generated resumes
- Failed extractions

## Troubleshooting

### Pipeline not running at scheduled time

1. Check if cron/systemd is running:
   ```bash
   # Cron
   crontab -l
   
   # Systemd
   sudo systemctl status job-search
   ```

2. Check logs for errors

3. Verify API keys are set in `.env`

### Web server not accessible

1. Check if port is open:
   ```bash
   netstat -tlnp | grep 5000
   ```

2. Check firewall:
   ```bash
   sudo ufw allow 5000
   ```

### Resume generation fails

1. Check `data/resume_config.yaml` exists
2. Check `data/projects.json` exists
3. Verify LaTeX is installed:
   ```bash
   python check_pdf_setup.py
   ```

## Configuration Files

Make sure these files are configured:

1. **`.env`** - API keys
   ```
   GOOGLE_API_KEY=your_key
   GOOGLE_CSE_ID=your_cse_id
   OPENAI_API_KEY=your_key
   ```

2. **`data/resume_config.yaml`** - Your resume details

3. **`data/projects.json`** - Your project portfolio

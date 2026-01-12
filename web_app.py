#!/usr/bin/env python3
"""
Web Frontend for Job Search Pipeline

Flask web application to view jobs, resumes, and pipeline status.
Accessible from PC while running on Jetson Nano.

Usage:
    python web_app.py                    # Run on default port 5000
    python web_app.py --port 8080        # Run on custom port
    python web_app.py --host 0.0.0.0     # Allow external access (for Jetson Nano)
"""

import argparse
import sys
from flask import Flask, render_template, jsonify, request, send_file
from datetime import datetime
import json
from pathlib import Path

from src.storage import JobDatabase
from src.config import config
from src.pipeline import JobSearchPipeline

app = Flask(__name__)


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    """Get database statistics."""
    try:
        db = JobDatabase(config.database_path)
        stats = db.get_stats()
        db.close()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/jobs')
def get_jobs():
    """Get jobs with optional filters."""
    try:
        db = JobDatabase(config.database_path)
        
        # Parse query parameters
        min_score = request.args.get('min_score', type=int)
        max_yoe = request.args.get('max_yoe', type=int)
        company = request.args.get('company', type=str)
        location = request.args.get('location', type=str)
        remote = request.args.get('remote', type=bool)
        limit = request.args.get('limit', default=100, type=int)
        
        filters = {}
        if min_score is not None:
            filters['min_score'] = min_score
        if max_yoe is not None:
            filters['max_yoe'] = max_yoe
        if company:
            filters['company'] = company
        if location:
            filters['location'] = location
        if remote is not None:
            filters['remote'] = remote
        
        jobs = db.get_jobs(filters=filters, limit=limit)
        db.close()
        
        return jsonify(jobs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/jobs/<int:job_id>')
def get_job(job_id):
    """Get a specific job by ID."""
    try:
        db = JobDatabase(config.database_path)
        job = db.get_job_by_id(job_id)
        db.close()
        
        if job:
            return jsonify(job)
        else:
            return jsonify({"error": "Job not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/jobs/<int:job_id>/mark-applied', methods=['POST'])
def mark_applied(job_id):
    """Mark a job as applied."""
    try:
        db = JobDatabase(config.database_path)
        success = db.mark_applied(job_id)
        db.close()
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Failed to update"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/unextracted')
def get_unextracted():
    """Get unextracted jobs."""
    try:
        db = JobDatabase(config.database_path)
        max_retries = request.args.get('max_retries', type=int)
        limit = request.args.get('limit', default=100, type=int)
        
        jobs = db.get_unextracted_jobs(limit=limit, max_retries=max_retries)
        db.close()
        
        return jsonify(jobs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/resumes')
def get_resumes():
    """Get generated resumes."""
    try:
        db = JobDatabase(config.database_path)
        resumes = db.get_resumes_summary()
        db.close()
        
        return jsonify(resumes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/resumes/<int:resume_id>/pdf')
def get_resume_pdf(resume_id):
    """Download resume PDF."""
    try:
        db = JobDatabase(config.database_path)
        resumes = db.get_all_resumes(limit=1000)
        db.close()
        
        resume = next((r for r in resumes if r['id'] == resume_id), None)
        if not resume or not resume.get('pdf_path'):
            return jsonify({"error": "PDF not found"}), 404
        
        pdf_path = Path(resume['pdf_path'])
        if pdf_path.exists():
            return send_file(str(pdf_path), mimetype='application/pdf')
        else:
            return jsonify({"error": "PDF file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/search/run', methods=['POST'])
def run_search():
    """Run a job search."""
    try:
        data = request.get_json() or {}
        keywords = data.get('keywords', ['AI engineer', 'ML engineer'])
        num_results = data.get('num_results', 50)
        min_score = data.get('min_score', 30)
        
        pipeline = JobSearchPipeline()
        summary = pipeline.run_daily() if not data.get('custom') else pipeline.run(
            keywords=keywords,
            num_results=num_results,
            min_score=min_score
        )
        pipeline.cleanup()
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Job Search Pipeline Web Interface")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    app.run(host=args.host, port=args.port, debug=args.debug)

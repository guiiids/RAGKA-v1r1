# Logging & Feedback Fallback Implementation Plan

This document outlines the step-by-step plan to add persistent usage logs, error logs, and a JSON fallback of feedback to our RAG application.

---

## 1. Define Docker Volumes

1. **Usage logs volume**  
   - Name: `azure-rag-usage-logs`  
   - Mount point: `/app/logs/usage`  

2. **Error logs volume**  
   - Name: `azure-rag-error-logs`  
   - Mount point: `/app/logs/errors`  

3. **Feedback fallback volume**  
   - Name: `azure-rag-feedback-fallback`  
   - Mount point: `/app/data/fallback`  

_Update `docker-compose.yml` under `web.volumes` and top-level `volumes`._

---

## 2. Add Dependencies

Install two new Python packages:

- **python-json-logger**: JSON formatter for Python’s logging  
- **APScheduler**: Scheduler for periodic tasks  

_Update `requirements.txt` accordingly._

---

## 3. Configure JSON-formatted File Handlers

In `main.py`, after the existing console/file handlers:

1. Import:
   ```python
   from logging.handlers import RotatingFileHandler
   from pythonjsonlogger import jsonlogger
   ```
2. Create a `JsonFormatter` instance.
3. Add two rotating handlers:
   - **Usage handler**  
     - Path: `/app/logs/usage/usage.log`  
     - Level: INFO  
     - Rotation: 10 MB, 5 backups  
   - **Error handler**  
     - Path: `/app/logs/errors/error.log`  
     - Level: ERROR  
     - Rotation: 10 MB, 5 backups  

---

## 4. Implement Feedback Export Script

Create `export_feedback.py` in project root:

- Connect to PostgreSQL via `db_manager.DatabaseManager.get_connection()`
- Query all rows from `votes`
- Atomically write JSON to `/app/data/fallback/feedback.json`:
  1. Write to `feedback.json.tmp`  
  2. Rename to `feedback.json`  

---

## 5. Schedule Export Job

Use APScheduler’s `BlockingScheduler`:

- **Initial run**: Immediately on startup  
- **Recurring**: Cron trigger at `minute=0` (hourly)

Users can invoke:
```bash
python export_feedback.py
```

---

## 6. Update Dockerfile / Docker Compose

1. **Docker Compose**  
   - Add a service or command to launch `export_feedback.py` in background:
     ```yaml
     command: >
       sh -c "python export_feedback.py & gunicorn main:app --bind 0.0.0.0:8000"
     ```
2. **Dockerfile**  
   - Ensure APScheduler and python-json-logger are installed.  

---

## 7. Testing & Validation

1. **Local run**  
   - Start the stack: `docker-compose up --build`
   - Verify volumes exist: `docker volume ls`
2. **Log files**  
   - Check `/app/logs/usage/usage.log` for INFO entries  
   - Check `/app/logs/errors/error.log` for ERROR entries  
3. **Feedback fallback**  
   - After an hour (or force run), confirm `/app/data/fallback/feedback.json` contents  

---

## 8. Future Considerations

- Expose a new API endpoint to download the fallback JSON.  
- Add cleanup or retention policies for log volumes.  
- Monitor volume size and integrate alerts.  

---

_By following this plan, we ensure durable storage of usage analytics, robust error tracking, and a JSON fallback of user feedback for recovery or migration._

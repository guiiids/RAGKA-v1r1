# Changelog

## [Unreleased] Feedback & Logging Enhancements
- Add volumes: `azure-rag-usage-logs`, `azure-rag-error-logs`, `azure-rag-feedback-fallback`
- Install `python-json-logger`, `APScheduler`
- Configure JSON-formatted usage and error loggers
- Create `export_feedback.py` with hourly APScheduler job
- Mount fallback JSON at `/app/data/fallback/feedback.json`

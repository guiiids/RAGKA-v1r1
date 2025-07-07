# Main.py Refactoring Plan - 4 Phase Implementation

## Overview
Refactor the mammoth main.py file (1000+ lines) into a modular, maintainable Flask application structure.

## Phase 0: Template Extraction (IMMEDIATE) ✅
**Goal**: Move HTML template from main.py to templates/index.html
**Impact**: Reduces main.py by ~600 lines immediately

### Tasks
- [x] Extract HTML_TEMPLATE variable to templates/index.html
- [x] Update index() route to use render_template()
- [x] Test application functionality
- [x] Verify all template variables work correctly

### Files Modified
- `main.py` - Remove HTML_TEMPLATE, update index() route
- `templates/index.html` - Replace with full SAGE template

---

## Phase 1: Service Layer Extraction
**Goal**: Extract business logic into service modules
**Impact**: Separates concerns, improves testability

### Files to Create
```
services/
├── __init__.py
├── llm_service.py          # LLM helper functions
├── analytics_service.py    # Analytics data processing
└── session_service.py      # Session management logic
```

### Tasks Checklist
- [ ] Create services/ directory structure
- [ ] Extract llm_helpee() and llm_helpee_2xl() functions
- [ ] Extract get_analytics_data() and export functions
- [ ] Extract session management logic (get_rag_assistant)
- [ ] Update imports in main.py
- [ ] Test all service functions work independently

### Functions to Move
**To llm_service.py:**
- `llm_helpee(input_text: str) -> str`
- `llm_helpee_2xl(input_text: str) -> str`

**To analytics_service.py:**
- `get_analytics_data(start_date=None, end_date=None)`
- `export_as_csv(analytics_data, timestamp)`
- `export_as_excel(analytics_data, timestamp)`

**To session_service.py:**
- `get_rag_assistant(session_id)`
- Session management dictionary and cleanup logic

---

## Phase 2: API Blueprint Separation
**Goal**: Split API endpoints into logical blueprints
**Impact**: Organizes routes by functionality, enables team development

### Files to Create
```
api/
├── __init__.py
├── query_routes.py      # Query and streaming endpoints
├── analytics_routes.py  # Analytics and dashboard endpoints
├── feedback_routes.py   # Feedback endpoints
└── magic_routes.py      # Magic query enhancement endpoints
```

### Tasks Checklist
- [ ] Create api/ directory structure
- [ ] Move query endpoints (/api/query, /api/stream_query, /api/clear_history)
- [ ] Move analytics endpoints (/analytics, /api/analytics, /api/analytics/export)
- [ ] Move feedback endpoint (/api/feedback)
- [ ] Move magic query endpoints (/api/magic_query, /api/magic_query_2xl)
- [ ] Move utility routes (/rag_logs, /api/rag_logs)
- [ ] Register blueprints in main.py
- [ ] Test all API endpoints work correctly

### Routes Distribution
**query_routes.py:**
- `/api/query` (POST)
- `/api/stream_query` (POST)
- `/api/clear_history` (POST)

**analytics_routes.py:**
- `/analytics` (GET)
- `/api/analytics` (GET)
- `/api/analytics/export` (GET)
- `/rag_logs` (GET)
- `/api/rag_logs` (GET)

**feedback_routes.py:**
- `/api/feedback` (POST)

**magic_routes.py:**
- `/api/magic_query` (POST)
- `/api/magic_query_2xl` (POST)

---

## Phase 3: Configuration and Constants
**Goal**: Centralize configuration and constants
**Impact**: Easier configuration management, cleaner code

### Files to Create
```
config/
├── __init__.py
├── app_config.py        # Logging setup and Flask configuration
└── constants.py         # System prompts and static values

utils/
├── __init__.py
└── helpers.py           # Utility functions
```

### Tasks Checklist
- [ ] Create config/ and utils/ directories
- [ ] Extract logging configuration setup
- [ ] Move PROMPT_ENHANCER_SYSTEM_MESSAGE constants
- [ ] Extract utility functions
- [ ] Update imports throughout application
- [ ] Test configuration loading works correctly

### Content to Move
**To constants.py:**
- `PROMPT_ENHANCER_SYSTEM_MESSAGE`
- `PROMPT_ENHANCER_SYSTEM_MESSAGE_2XL`
- `MARKED_JS_CDN`

**To app_config.py:**
- Logging setup code
- Flask app configuration
- Environment variable loading

**To helpers.py:**
- Static file serving functions
- Utility helper functions

---

## Phase 4: Final Cleanup and Optimization
**Goal**: Clean up main.py and optimize structure
**Impact**: Minimal, clean main.py file (~100-150 lines)

### Tasks Checklist
- [ ] Remove unused imports from main.py
- [ ] Add proper docstrings to all modules
- [ ] Create __init__.py files for packages
- [ ] Add error handling for missing modules
- [ ] Test complete application functionality
- [ ] Performance testing
- [ ] Documentation update

### Final main.py Structure
```python
# main.py (target: ~100-150 lines)
from flask import Flask
from config.app_config import setup_logging, configure_app
from api.query_routes import query_bp
from api.analytics_routes import analytics_bp
from api.feedback_routes import feedback_bp
from api.magic_routes import magic_bp

app = Flask(__name__)
configure_app(app)
setup_logging()

# Register blueprints
app.register_blueprint(query_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(magic_bp)

@app.route("/")
def index():
    return render_template('index.html', ...)

if __name__ == "__main__":
    app.run(...)
```

---

## Testing Strategy
Each phase includes testing checkpoints:
1. **Unit Tests**: Test individual functions in isolation
2. **Integration Tests**: Test module interactions
3. **End-to-End Tests**: Test complete user workflows
4. **Performance Tests**: Ensure no performance degradation

## Rollback Strategy
- Keep backup of original main.py as main_backup.py
- Each phase can be rolled back independently
- Git commits after each successful phase

## Success Metrics
- **Code Reduction**: main.py reduced from 1000+ to ~150 lines
- **Maintainability**: Each module has single responsibility
- **Testability**: Individual components can be unit tested
- **Performance**: No degradation in response times
- **Functionality**: All existing features work correctly

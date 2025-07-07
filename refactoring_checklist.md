# Main.py Refactoring Checklist

## Phase 0: Template Extraction ✅ COMPLETE
- [x] **Backup original main.py** → `main_backup.py`
- [x] **Extract HTML_TEMPLATE** → Move to `templates/index.html`
- [x] **Update index() route** → Use `render_template()` instead of `render_template_string()`
- [x] **Test template variables** → Verify `file_executed`, `sas_token`, `marked_js_cdn` work
- [x] **Test application startup** → Ensure no errors on launch
- [x] **Test web interface** → Verify UI loads correctly

**Checkpoint**: Application runs with template extracted ✅

---

## Phase 1: Service Layer Extraction
### Setup
- [ ] **Create services directory** → `mkdir services`
- [ ] **Create services/__init__.py** → Empty init file

### LLM Service
- [ ] **Create services/llm_service.py**
- [ ] **Move llm_helpee() function** → Extract from main.py
- [ ] **Move llm_helpee_2xl() function** → Extract from main.py
- [ ] **Move PROMPT_ENHANCER constants** → Extract system messages
- [ ] **Update imports in main.py** → Import from services.llm_service
- [ ] **Test LLM service functions** → Verify magic buttons work

### Analytics Service
- [ ] **Create services/analytics_service.py**
- [ ] **Move get_analytics_data() function** → Extract from main.py
- [ ] **Move export_as_csv() function** → Extract from main.py
- [ ] **Move export_as_excel() function** → Extract from main.py
- [ ] **Update imports in main.py** → Import from services.analytics_service
- [ ] **Test analytics functions** → Verify dashboard and exports work

### Session Service
- [ ] **Create services/session_service.py**
- [ ] **Move rag_assistants dictionary** → Extract global variable
- [ ] **Move get_rag_assistant() function** → Extract from main.py
- [ ] **Update imports in main.py** → Import from services.session_service
- [ ] **Test session management** → Verify conversations work

**Checkpoint**: All services work independently ⏳

---

## Phase 2: API Blueprint Separation
### Setup
- [ ] **Create api directory** → `mkdir api`
- [ ] **Create api/__init__.py** → Empty init file

### Query Routes Blueprint
- [ ] **Create api/query_routes.py**
- [ ] **Move /api/query route** → Extract POST endpoint
- [ ] **Move /api/stream_query route** → Extract POST endpoint
- [ ] **Move /api/clear_history route** → Extract POST endpoint
- [ ] **Create query_bp blueprint** → Flask Blueprint object
- [ ] **Register query_bp in main.py** → app.register_blueprint()
- [ ] **Test query endpoints** → Verify chat functionality

### Analytics Routes Blueprint
- [ ] **Create api/analytics_routes.py**
- [ ] **Move /analytics route** → Extract GET endpoint
- [ ] **Move /api/analytics route** → Extract GET endpoint
- [ ] **Move /api/analytics/export route** → Extract GET endpoint
- [ ] **Move /rag_logs route** → Extract GET endpoint
- [ ] **Move /api/rag_logs route** → Extract GET endpoint
- [ ] **Create analytics_bp blueprint** → Flask Blueprint object
- [ ] **Register analytics_bp in main.py** → app.register_blueprint()
- [ ] **Test analytics endpoints** → Verify dashboard and logs

### Feedback Routes Blueprint
- [ ] **Create api/feedback_routes.py**
- [ ] **Move /api/feedback route** → Extract POST endpoint
- [ ] **Create feedback_bp blueprint** → Flask Blueprint object
- [ ] **Register feedback_bp in main.py** → app.register_blueprint()
- [ ] **Test feedback endpoint** → Verify thumbs up/down work

### Magic Routes Blueprint
- [ ] **Create api/magic_routes.py**
- [ ] **Move /api/magic_query route** → Extract POST endpoint
- [ ] **Move /api/magic_query_2xl route** → Extract POST endpoint
- [ ] **Create magic_bp blueprint** → Flask Blueprint object
- [ ] **Register magic_bp in main.py** → app.register_blueprint()
- [ ] **Test magic endpoints** → Verify magic wand buttons work

### Static Routes
- [ ] **Move /assets/<path:filename> route** → Keep in main.py or move to utils
- [ ] **Move /static/<path:filename> route** → Keep in main.py or move to utils

**Checkpoint**: All API endpoints work through blueprints ⏳

---

## Phase 3: Configuration and Constants
### Setup
- [ ] **Create config directory** → `mkdir config`
- [ ] **Create config/__init__.py** → Empty init file
- [ ] **Create utils directory** → `mkdir utils`
- [ ] **Create utils/__init__.py** → Empty init file

### App Configuration
- [ ] **Create config/app_config.py**
- [ ] **Move logging setup code** → Extract logger configuration
- [ ] **Move Flask app configuration** → Extract app.secret_key, etc.
- [ ] **Create setup_logging() function** → Centralize logging setup
- [ ] **Create configure_app() function** → Centralize Flask config
- [ ] **Update main.py imports** → Import from config.app_config

### Constants
- [ ] **Create config/constants.py**
- [ ] **Move MARKED_JS_CDN constant** → Extract from main.py
- [ ] **Move any other constants** → Extract static values
- [ ] **Update imports throughout** → Import constants where needed

### Utilities
- [ ] **Create utils/helpers.py**
- [ ] **Move serve_assets() function** → Extract static file serving
- [ ] **Move serve_static() function** → Extract static file serving
- [ ] **Update main.py imports** → Import from utils.helpers

**Checkpoint**: Configuration is centralized ⏳

---

## Phase 4: Final Cleanup and Optimization
### Code Cleanup
- [ ] **Remove unused imports** → Clean up main.py imports
- [ ] **Add docstrings** → Document all new modules
- [ ] **Add type hints** → Improve code documentation
- [ ] **Add error handling** → Handle missing modules gracefully

### Testing
- [ ] **Unit test services** → Test individual service functions
- [ ] **Integration test blueprints** → Test API endpoints
- [ ] **End-to-end test** → Test complete user workflows
- [ ] **Performance test** → Ensure no degradation
- [ ] **Load test** → Test under concurrent users

### Documentation
- [ ] **Update README.md** → Document new structure
- [ ] **Create module documentation** → Document each new module
- [ ] **Update deployment docs** → Update any deployment scripts

### Final Verification
- [ ] **Check main.py line count** → Should be ~100-150 lines
- [ ] **Verify all features work** → Complete functional test
- [ ] **Check error logs** → No errors on startup
- [ ] **Performance benchmark** → Compare before/after

**Checkpoint**: Refactoring complete and verified ⏳

---

## Scripts Usage Status

### ✅ ACTIVE (Production Use)
- `main.py` - Primary Flask application
- `rag_assistant_with_history.py` - Core RAG functionality
- `db_manager.py` - Database operations
- `config.py` - Configuration management
- `openai_service.py` - OpenAI API wrapper

### ⚠️ EVALUATION/TESTING (Development Use)
- `compare_rag_implementations.py` - Performance comparison
- `test_rag_consistency.py` - Consistency testing
- `test_rag_improvement.py` - Improvement testing
- `analyze_rag_consistency.py` - Analysis tool
- `rag_improvement_logging.py` - Logging analysis

### 📋 BACKUP/ALTERNATE (Not Currently Used)
- `main_alternate.py` - Backup version
- `main2.py` - Alternative implementation
- `rag_assistant_with_history_alternate.py` - Alternative RAG
- `rag_assistant_with_history_copy.py` - Backup copy
- `app.py` - Alternative Flask app

### 🔧 UTILITY (Occasional Use)
- `run_improved_rag.sh` - Deployment script
- `run_comparison.sh` - Comparison runner
- `run_all_tests.sh` - Test runner
- `parse_prompts.py` - Prompt parsing utility

---

## Rollback Plan
If any phase fails:
1. **Stop immediately** - Don't proceed to next phase
2. **Restore from backup** - Use main_backup.py
3. **Identify issue** - Debug the specific problem
4. **Fix and retry** - Address issue and retry phase
5. **Test thoroughly** - Ensure fix works before continuing

## Success Criteria
- [ ] **main.py reduced** from 1000+ lines to ~150 lines
- [ ] **All functionality preserved** - No features broken
- [ ] **Performance maintained** - No slowdown
- [ ] **Code maintainability improved** - Easier to modify
- [ ] **Testing enabled** - Individual components testable

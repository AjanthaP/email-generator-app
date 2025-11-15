# Changelog

All notable changes to the Email Generator App project.

---

## [Recent Updates] - 2024

### Developer Mode Implementation
- **Feature**: Added LLM output tracing for workflow debugging
- **Implementation**:
  - Added `developer_mode` parameter to `execute_workflow()` and `generate_email()` in `langgraph_flow.py`
  - When `developer_mode=True`, captures per-agent snapshots in `developer_trace` list
  - Each trace entry contains: `{"agent": "agent_name", "snapshot": {...}}` with LLM outputs
  - Returns trace in response: `{"email": {...}, "developer_trace": [...]}`
- **Frontend Guide**: See `REACT_DEVELOPER_MODE.md` for React implementation details

### Streamlit Removal
- **Removed Files**:
  - `src/ui/streamlit_app.py` - Full Streamlit UI application
  - `src/auth/streamlit_auth.py` - Streamlit authentication helpers
  - `src/ui/` folder - Entire directory removed
- **Reason**: No longer using Streamlit UI; migrated to React frontend

### API Structure Simplification
- **Changed**: Removed `/api/v1/` prefix from all endpoints
- **New Endpoint Structure**:
  - Email: `/api/v1/email/*` → `/email/*`
  - Users: `/api/v1/users/*` → `/users/*`
  - Auth: `/auth/*` (unchanged)
  - Debug: `/api/debug/*` → `/debug/*`
- **Backend Changes** (`src/api/main.py`):
  - Updated all router prefixes to direct paths
  - Updated root endpoint documentation
- **Frontend Changes** (`frontend/src/lib/api.ts`):
  - Updated all API calls to match new backend paths:
    - `generateEmail()`: `/email/generate`
    - `getUserProfile()`: `/users/{userId}/profile`
    - `getDraftHistory()`: `/users/{userId}/history`
    - Auth endpoints: `/auth/*`

### Documentation Updates
- **Updated Files**:
  - `README.md`: Removed Streamlit references, updated API examples with new endpoints
  - `RAILWAY_DEPLOYMENT.md`: Updated curl examples with direct endpoint paths
  - `POSTGRESQL_SETUP_RAILWAY.md`: Updated endpoint references
  - `frontend/README.md`: Updated API integration documentation
  - `DRAFT_HISTORY_INVESTIGATION.md`: Updated endpoint references
- **New Documentation**:
  - `REACT_DEVELOPER_MODE.md`: Complete guide for implementing developer mode in React frontend

---

## [Previous Updates] - Historical Changes

### Authentication & Authorization
- Implemented OAuth 2.0 authentication with JWT tokens
- Added user profile management and session handling
- Created authentication middleware and security utilities
- See: `OAUTH_SETUP_CHECKLIST.md` for OAuth configuration

### Database Migration
- Migrated from SQLite to PostgreSQL
- Railway deployment with PostgreSQL integration
- Updated all database queries and schema
- See: `POSTGRESQL_SETUP_RAILWAY.md` for setup details

### Frontend Development
- Built React frontend with Vite
- Implemented responsive UI with Tailwind CSS
- Added API client with TypeScript
- Deployed to Railway with environment variable management
- See: `FRONTEND_DEPLOYMENT.md` for deployment guide

### LangGraph Workflow
- 8-agent email generation pipeline:
  1. Input Parser
  2. Intent Detector
  3. Draft Writer
  4. Tone Stylist
  5. Personalization Agent
  6. Review Agent
  7. Refinement Agent
  8. Router
- Integrated OpenAI API for LLM operations
- Added memory management and user profile storage

### Testing & Validation
- Created comprehensive test suite (`test_agents.py`, `test_agents_structure.py`)
- Validated agent implementations and workflow integration
- See: `TESTING_VALIDATION_REPORT.md` for test results

### Deployment Infrastructure
- Railway deployment for both backend (FastAPI) and frontend (React)
- Environment variable configuration with `.env` files
- PostgreSQL database hosting
- CORS configuration for cross-origin requests
- See: `RAILWAY_DEPLOYMENT.md` for deployment instructions

---

## Migration Notes

### OpenAI Configuration
- Migrated from Anthropic to OpenAI
- Updated `config.py` with OpenAI API key management
- All agents now use GPT models
- See: `OPENAI_MIGRATION_ANALYSIS.md` for details

### ChromaDB Integration (Future)
- Planned integration for vector storage and semantic search
- See: `CHROMADB_FUTURE_INTEGRATION.md` for implementation roadmap

---

## Troubleshooting

### Common Issues
1. **API Quota Errors**: Check OpenAI API quota and billing status
2. **CORS Issues**: Verify `FRONTEND_URL` in backend `.env` matches actual frontend URL
3. **Database Connection**: Ensure `DATABASE_URL` is correctly configured in Railway
4. **Authentication Failures**: Verify OAuth credentials and JWT secret configuration

### Debugging
- Enable developer mode in workflow for detailed LLM traces
- Check Railway logs for backend errors
- Use browser DevTools Network tab for API request debugging
- Verify environment variables are set correctly in Railway

---

## Maintenance

### Regular Tasks
- Monitor OpenAI API usage and costs
- Review Railway deployment logs
- Update dependencies in `requirements.txt` and `frontend/package.json`
- Backup PostgreSQL database regularly

### Security
- Rotate JWT secrets periodically
- Keep OAuth credentials secure
- Review CORS configuration for production
- Update dependencies for security patches

---

## Contributors
- AI Agent: Implementation, refactoring, and documentation
- User (Merwin): Architecture decisions, guides (v2/v3), and project direction

---

_Last Updated: 2024_

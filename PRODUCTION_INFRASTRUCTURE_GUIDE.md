# Production Infrastructure Guide

## Infrastructure Components Implemented

### 1. **Caching Layer - Redis**

**Why Redis?**
- High-performance in-memory caching
- Built-in data expiration (TTL)
- Support for complex data types
- Horizontal scaling capabilities
- Battle-tested in production

**What we implemented:**
```python
# src/cache/redis_cache.py
- Session caching with automatic expiration
- User profile caching for quick access
- Email draft caching for auto-save functionality
- LLM response caching to reduce API costs
- Rate limiting with sliding window
- Cache metrics and monitoring
```

**Production setup:**
```bash
# Docker deployment
docker run -d --name redis-cache \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine redis-server --appendonly yes

# Or managed service
# AWS ElastiCache, Google Cloud Memorystore, Azure Cache for Redis
```

### 2. **Context Storage - ChromaDB**

**Why ChromaDB?**
- Vector database optimized for AI applications
- Built-in embedding generation
- Semantic search capabilities
- Easy integration with LangChain
- Local and cloud deployment options

**What we implemented:**
```python
# src/context/chroma_context.py
- Email context storage with vector embeddings
- Conversation history with semantic search
- User preference learning
- Similar email retrieval
- Context-aware suggestions
```

**Production considerations:**
```python
# Persistent storage with proper backup
persist_directory = "/app/data/chromadb"

# Or use Chroma Cloud for managed service
# https://trychroma.com/
```

### 3. **Email Integration - Gmail API**

**Why Gmail?**
- Most widely used email service
- Comprehensive API with OAuth 2.0
- Support for drafts, sending, and reading
- Thread management capabilities
- Rich metadata and search

**What we implemented:**
```python
# src/integrations/gmail_service.py
- OAuth 2.0 authentication flow
- Send emails with HTML/text content
- Draft management (create, update, send)
- Email context retrieval for replies
- Thread context for conversations
```

**Setup requirements:**
```json
// config/gmail_credentials.json
{
  "web": {
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "redirect_uris": ["http://localhost:8501/oauth/callback"]
  }
}
```

### 4. **Tool Integration - MCP (Model Context Protocol)**

**Why MCP?**
- Emerging standard for AI tool integration
- Allows other AI systems to use your email generator
- Enables composition with other AI tools
- Future-proof architecture
- Protocol-level interoperability

**What we implemented:**
```python
# src/integrations/mcp_integration.py
- MCP Server exposing email generation as tools
- MCP Client for consuming external tools
- Tool registry (generate_email, get_templates, analyze_context)
- Resource registry (user profiles, templates, history)
- Prompt registry (professional email, follow-up templates)
```

**Usage example:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "generate_email",
    "arguments": {
      "user_id": "user123",
      "prompt": "Write a follow-up email about the project proposal",
      "tone": "professional",
      "recipient": "client@company.com"
    }
  }
}
```

### 5. **OAuth Authentication**

**Why OAuth 2.0?**
- Industry standard for secure authentication
- No password storage required
- Scoped permissions
- Token refresh capabilities
- Support for multiple providers

**What we implemented:**
```python
# src/auth/oauth_providers.py
- Google OAuth (recommended for Gmail integration)
- GitHub OAuth (for developer users)
- Microsoft OAuth (for enterprise users)
- Multi-provider management
- Token refresh handling
```

**Recommended approach:**
**Use Google OAuth** for your email application because:
- Seamless Gmail integration
- Single sign-on experience
- Access to Google Workspace APIs
- Familiar to most users

## Integration Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   FastAPI API   │    │   Background    │
│                 │    │                 │    │   Workers       │
│ - OAuth login   │◄──►│ - Authentication│◄──►│ - Email queue   │
│ - Email forms   │    │ - Rate limiting │    │ - Cache warmup  │
│ - Chat interface│    │ - API endpoints │    │ - Metrics       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redis Cache   │    │   ChromaDB      │    │   Gmail API     │
│                 │    │                 │    │                 │
│ - Sessions      │    │ - Email context │    │ - Send emails   │
│ - User profiles │    │ - Conversations │    │ - Manage drafts │
│ - Draft cache   │    │ - Preferences   │    │ - Read history  │
│ - Rate limits   │    │ - Similarities  │    │ - Thread context│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Deployment Strategy

### Development Environment
```bash
# Install dependencies
pip install redis chromadb google-api-python-client google-auth-oauthlib requests

# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Run application
streamlit run src/ui/streamlit_app.py
```

### Production Environment

#### Option 1: Container-based (Recommended)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "src/ui/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  email-app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - REDIS_URL=redis://redis:6379
      - CHROMADB_PERSIST_DIR=/app/data/chromadb
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    depends_on:
      - redis
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes

volumes:
  redis-data:
```

#### Option 2: Cloud-native

**Google Cloud Platform:**
```bash
# Use Cloud Run for app
gcloud run deploy email-generator \
  --image gcr.io/PROJECT/email-app \
  --platform managed \
  --set-env-vars REDIS_URL="redis://MEMORYSTORE_IP:6379"

# Use Memorystore for Redis
gcloud redis instances create email-cache \
  --size=1 \
  --region=us-central1

# Use Cloud Storage for ChromaDB persistence
```

**AWS:**
```bash
# Use ECS/Fargate for app
aws ecs create-service \
  --cluster email-cluster \
  --service-name email-generator \
  --task-definition email-app:1

# Use ElastiCache for Redis
aws elasticache create-replication-group \
  --replication-group-id email-cache \
  --description "Email app cache"

# Use EFS for ChromaDB persistence
```

## Configuration Management

### Environment Variables
```bash
# Required
GOOGLE_CLIENT_ID=your-oauth-client-id
GOOGLE_CLIENT_SECRET=your-oauth-client-secret
GEMINI_API_KEY=your-gemini-api-key

# Optional
REDIS_URL=redis://localhost:6379
CHROMADB_PERSIST_DIR=./data/chromadb
DISABLE_OAUTH=false
DISABLE_GMAIL=false
DISABLE_CHROMADB=false

# Production
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=60
CACHE_TTL_SECONDS=3600
```

### Configuration Files Structure
```
config/
├── oauth_config.json          # OAuth provider settings
├── gmail_credentials.json     # Gmail API credentials  
├── app_config.yaml           # Application settings
└── production_config.yaml   # Production overrides
```

## Monitoring and Observability

### Metrics to Track
```python
# Application Metrics
- Email generation requests/minute
- Cache hit/miss ratios
- Authentication success/failure rates
- API response times
- Error rates by component

# Infrastructure Metrics  
- Redis memory usage
- ChromaDB query performance
- Gmail API quota usage
- OAuth token refresh rates
```

### Logging Strategy
```python
import logging
import structlog

# Structured logging for production
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Key events to log
- User authentication events
- Email generation requests
- Cache operations
- External API calls
- Error conditions
```

## Security Considerations

### Data Protection
```python
# Encrypt sensitive data at rest
- OAuth tokens (use encryption at rest)
- User email content (consider end-to-end encryption)
- Personal information (PII handling)

# Secure transmission
- HTTPS only in production
- Proper CORS configuration
- Secure cookie settings
```

### Access Control
```python
# Multi-tenant isolation
- User data segregation
- Rate limiting per user
- Resource quotas
- Audit logging
```

## Cost Optimization

### Caching Strategy
```python
# Reduce LLM API costs
- Cache similar prompts
- Implement prompt deduplication  
- Use cheaper models for simple tasks

# Optimize storage costs
- Implement data retention policies
- Compress stored contexts
- Use tiered storage
```

### Resource Management
```python
# Right-size infrastructure
- Monitor actual usage patterns
- Use auto-scaling groups
- Implement graceful degradation
- Cache warming strategies
```

## Getting Started

1. **Set up OAuth credentials** (Google Cloud Console)
2. **Deploy Redis cache** (Docker or managed service)
3. **Configure ChromaDB** (local or Chroma Cloud)
4. **Update configuration files** with your settings
5. **Deploy application** using Docker Compose or cloud provider
6. **Set up monitoring** and logging
7. **Test email integration** with Gmail API

This infrastructure provides enterprise-grade capabilities while maintaining simplicity for development and deployment.
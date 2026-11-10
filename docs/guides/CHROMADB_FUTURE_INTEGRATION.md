# ChromaDB Future Integration Guide

> **Note:** This is a planning document for future ChromaDB integration.  
> Your app currently uses PostgreSQL for all storage. ChromaDB can be added later for semantic search capabilities.

---

## 🎯 When to Add ChromaDB

Add ChromaDB when you want these features:
- **Semantic Search**: "Find all emails about project proposals" (meaning-based, not keyword)
- **Similar Draft Discovery**: "Show me 5 emails with similar tone to this one"
- **Context Retrieval**: Give AI relevant past drafts as examples for new emails
- **Smart Suggestions**: "Users who wrote emails like this also used these templates"

---

## 🏗️ Architecture: PostgreSQL + ChromaDB Together

### PostgreSQL (Already Implemented) ✅
**Stores:** Structured data
- User profiles (name, email, company, role)
- Draft text and metadata (tone, length, recipient)
- Timestamps and relationships
- OAuth sessions

**Best for:**
- Exact matches: "Get user by email"
- Sorting/filtering: "Show drafts from last 7 days"
- Aggregations: "Count total drafts per user"
- Transactions: Ensure data consistency

### ChromaDB (Future Addition) 🔮
**Stores:** Vector embeddings of draft content
- Converts email text to numerical vectors (embeddings)
- Enables similarity search by meaning
- Lightweight, no heavy infrastructure

**Best for:**
- Semantic search: "Find emails about quarterly reviews" (matches synonyms, context)
- Similarity: "Find drafts like this" (by meaning, not exact words)
- RAG: Retrieve relevant past emails as context for AI generation

---

## 🔄 How They Work Together

```
User Request: "Generate email about project deadline extension"
    ↓
1. PostgreSQL: Load user profile (name, company, role, preferences)
    ↓
2. ChromaDB: Search for similar past drafts about "deadlines" or "extensions"
    ↓
3. AI Agent: Use profile + similar drafts as context → Generate new email
    ↓
4. PostgreSQL: Save new draft with metadata
    ↓
5. ChromaDB: Store embedding of new draft for future similarity search
```

**Key Design:**
- PostgreSQL has the `draft.id` primary key
- ChromaDB stores embeddings with metadata `{"draft_id": 123, "user_id": "user_abc"}`
- Queries: ChromaDB finds similar draft IDs → PostgreSQL fetches full draft details

---

## 📦 Implementation Plan (When Ready)

### Phase 1: Setup ChromaDB (15 minutes)

1. **Already in requirements.txt** ✅
   ```python
   chromadb>=0.4.18  # Already installed
   ```

2. **Create ChromaDB client** (new file: `src/db/chromadb_client.py`)
   ```python
   import chromadb
   from chromadb.config import Settings
   
   client = chromadb.PersistentClient(
       path="data/chromadb",  # Local storage
       settings=Settings(anonymized_telemetry=False)
   )
   
   collection = client.get_or_create_collection(
       name="email_drafts",
       metadata={"description": "Email draft embeddings"}
   )
   ```

3. **Railway persistent volume** (if deployed)
   - Add persistent volume to Railway project ($5/month)
   - Mount at `/app/data/chromadb`
   - OR use ChromaDB cloud (free tier available)

### Phase 2: Add Embedding Generation (20 minutes)

Use Google's Generative AI (already have API key):

```python
# src/utils/embeddings.py
import google.generativeai as genai
from src.utils.config import settings

genai.configure(api_key=settings.gemini_api_key)

def get_embedding(text: str) -> list[float]:
    """Generate embedding for text using Gemini."""
    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    return result['embedding']
```

### Phase 3: Update MemoryManager (30 minutes)

Add ChromaDB operations alongside PostgreSQL:

```python
# src/memory/memory_manager.py

def save_draft(self, user_id: str, draft_data: Dict[str, Any]) -> None:
    # Save to PostgreSQL (existing code)
    draft_id = self._save_draft_db(user_id, draft_data)
    
    # NEW: Save embedding to ChromaDB
    if self.chromadb_enabled:
        self._save_draft_embedding(draft_id, user_id, draft_data['content'])

def _save_draft_embedding(self, draft_id: int, user_id: str, content: str):
    """Store draft embedding in ChromaDB."""
    from src.utils.embeddings import get_embedding
    from src.db.chromadb_client import collection
    
    embedding = get_embedding(content)
    collection.add(
        embeddings=[embedding],
        documents=[content],
        metadatas=[{"draft_id": draft_id, "user_id": user_id}],
        ids=[f"draft_{draft_id}"]
    )

def search_similar_drafts(self, user_id: str, query: str, limit: int = 5):
    """Find drafts similar to query text."""
    from src.utils.embeddings import get_embedding
    from src.db.chromadb_client import collection
    
    query_embedding = get_embedding(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        where={"user_id": user_id},
        n_results=limit
    )
    
    # Get full draft details from PostgreSQL
    draft_ids = [m['draft_id'] for m in results['metadatas'][0]]
    return self.load_drafts_by_ids(draft_ids)
```

### Phase 4: Update AI Agents (20 minutes)

Enhance draft generation with context from similar drafts:

```python
# src/agents/draft_writer.py

def generate_draft(self, user_input: str, user_profile: dict):
    # NEW: Find similar past drafts
    similar_drafts = self.memory.search_similar_drafts(
        user_id=user_profile['id'],
        query=user_input,
        limit=3
    )
    
    # Build enhanced prompt with examples
    context = "\n\n".join([
        f"Example {i+1}:\n{draft['content']}"
        for i, draft in enumerate(similar_drafts)
    ])
    
    prompt = f"""
    User Profile: {user_profile['name']} at {user_profile['company']}
    Request: {user_input}
    
    Similar emails you've written before:
    {context}
    
    Generate a new email matching the user's style...
    """
    
    # Rest of generation logic...
```

### Phase 5: Add Frontend Feature (30 minutes)

Add semantic search to history view:

```typescript
// frontend/src/lib/api.ts

export async function searchDrafts(query: string) {
  return apiCall<DraftSearchResult>('/api/v1/drafts/search', {
    method: 'POST',
    body: JSON.stringify({ query })
  });
}

// frontend/src/components/DraftHistory.tsx

<input 
  placeholder="Search drafts by meaning (e.g., 'meeting requests')"
  onChange={e => handleSemanticSearch(e.target.value)}
/>
```

---

## 💰 Cost Considerations

### Free Development
- **Local ChromaDB**: Free, stores in `data/chromadb/` folder
- **Gemini Embeddings**: Free tier (1500 requests/day)
- **PostgreSQL**: Railway free tier (5GB)

### Production Options

#### Option 1: ChromaDB on Railway with Persistent Volume
- **Cost**: $5/month for 10GB persistent volume
- **Pros**: Same infrastructure as PostgreSQL, simple setup
- **Cons**: Requires volume mount configuration

#### Option 2: ChromaDB Cloud (Hosted)
- **Cost**: Free tier (1GB vectors), then $50/month
- **Pros**: Managed service, auto-backups, no volume needed
- **Cons**: External dependency, potential latency

#### Option 3: Keep Local ChromaDB (Ephemeral)
- **Cost**: Free
- **Pros**: No additional cost
- **Cons**: Embeddings lost on restart (can rebuild from PostgreSQL)
- **Note**: Acceptable if you can regenerate embeddings from PostgreSQL drafts

---

## 🚀 Quick Start (When You're Ready)

1. **Enable ChromaDB in config:**
   ```bash
   # .env or Railway variables
   ENABLE_CHROMADB=true
   CHROMADB_PERSIST_DIR=data/chromadb
   ```

2. **Run embedding generation for existing drafts:**
   ```bash
   python scripts/generate_embeddings.py
   ```

3. **Test semantic search:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/drafts/search \
     -H "Content-Type: application/json" \
     -d '{"query": "meeting requests", "limit": 5}'
   ```

---

## 📊 Performance Impact

### Embedding Generation
- **Time**: ~200ms per draft (Google Gemini API)
- **When**: Async after saving draft (non-blocking)
- **Storage**: ~1KB per draft embedding

### Similarity Search
- **Time**: ~50-100ms for 1000 drafts
- **Scaling**: ChromaDB handles millions of vectors efficiently
- **Memory**: ~10MB per 1000 embeddings (in-memory)

---

## ✅ Current State vs. Future State

### ✅ Current (PostgreSQL Only)
```
User → Generate Email → Save to PostgreSQL → Show in History
                              ↓
                        Lost after restart on Railway
                        (unless persistent volume)
```

### 🔮 Future (PostgreSQL + ChromaDB)
```
User → Generate Email → Save to PostgreSQL → Save embedding to ChromaDB
                              ↓                        ↓
                        Persistent storage      Semantic search enabled
                              ↓                        ↓
                        Show in History ←  Find similar drafts for context
```

---

## 🎯 Bottom Line

- **Now:** PostgreSQL handles all storage ✅
- **Later:** Add ChromaDB for semantic search when you need it 🔮
- **No Conflicts:** They work together perfectly - PostgreSQL = source of truth, ChromaDB = search index
- **Low Risk:** ChromaDB is optional enhancement, doesn't replace PostgreSQL
- **Easy Migration:** Run one script to generate embeddings from existing PostgreSQL drafts

**Recommendation:** Use PostgreSQL for 2-3 months, gather real usage data, then decide if semantic search adds value. Most apps don't need it initially! 🚀

---

## 📚 Resources

- [ChromaDB Docs](https://docs.trychroma.com/)
- [Google Embeddings API](https://ai.google.dev/docs/embeddings_guide)
- [Gemini Pricing](https://ai.google.dev/pricing)

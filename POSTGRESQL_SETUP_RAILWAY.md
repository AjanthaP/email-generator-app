# PostgreSQL Setup Guide for Railway

This guide walks you through setting up PostgreSQL on Railway and configuring your Email Generator app to use it for persistent storage.

## 🎯 Why PostgreSQL?

- **Persistent Storage**: Data survives app restarts and redeployments
- **Free Tier**: Railway offers free PostgreSQL with 5GB storage
- **Auto-backups**: Railway handles backups automatically
- **Production-ready**: Scales with your app as usage grows
- **ChromaDB Compatible**: Use both PostgreSQL (structured data) + ChromaDB (semantic search) together

---

## 📋 Prerequisites

1. Railway account (free at [railway.app](https://railway.app))
2. Email Generator app deployed on Railway
3. 5 minutes of setup time

---

## 🚀 Step-by-Step Setup

### 1. Add PostgreSQL to Your Railway Project

#### Option A: Via Railway Dashboard (Recommended)

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click on your **email-generator-app** project
3. Click **+ New** button (top right)
4. Select **Database** → **Add PostgreSQL**
5. PostgreSQL will be provisioned in ~30 seconds

#### Option B: Via Railway CLI

```bash
railway add --database postgresql
```

### 2. Verify PostgreSQL Connection

Railway automatically creates a `DATABASE_URL` environment variable that connects to your new database.

1. In your Railway project dashboard, click on **PostgreSQL**
2. Go to **Variables** tab
3. You should see variables like:
   - `DATABASE_URL` (full connection string)
   - `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`

**Example DATABASE_URL format:**
```
postgresql://postgres:password123@containers-us-west-123.railway.app:5432/railway
```

### 3. Connect Your App to PostgreSQL

Railway automatically shares the `DATABASE_URL` variable with all services in the project. Your app will detect it on startup.

#### Verify Environment Variable Sharing

1. Go to your **email-generator-app** service (not the database)
2. Click **Variables** tab
3. Ensure `DATABASE_URL` appears in the list (it's shared from PostgreSQL service)

If it doesn't appear:
1. Click **+ New Variable**
2. Select **Reference** → Choose `DATABASE_URL` from PostgreSQL service
3. Click **Add**

### 4. Deploy Your App with PostgreSQL

Your latest code already supports PostgreSQL! Just redeploy:

```bash
git push origin master
```

Railway will auto-deploy with the new database connection.

### 5. Verify Database Initialization

Check Railway logs for your app:

1. Go to **email-generator-app** service
2. Click **Deployments** → Latest deployment → **View Logs**
3. Look for these startup messages:

```
[startup] Database connected: postgresql://***@containers-us-west-123.railway.app:5432/railway
Creating database tables...
Database tables ready
✓ Database initialized successfully
```

If you see `DATABASE_URL not configured - using JSON file storage`, the environment variable isn't set correctly.

---

## 🔄 Migrating Existing JSON Data

If you have existing user profiles or drafts in JSON files, migrate them:

### Option A: Run Migration Locally (Recommended)

1. Get DATABASE_URL from Railway:
   ```bash
   railway variables
   ```
   Copy the `DATABASE_URL` value

2. Create `.env` file locally:
   ```bash
   DATABASE_URL=postgresql://postgres:password@...railway.app:5432/railway
   ```

3. Run migration script:
   ```bash
   python scripts/migrate_json_to_postgres.py
   ```

### Option B: Run Migration on Railway

1. Connect to Railway shell:
   ```bash
   railway run bash
   ```

2. Run migration:
   ```bash
   python scripts/migrate_json_to_postgres.py
   ```

### Migration Output

You should see:
```
============================================================
Starting JSON to PostgreSQL migration
============================================================
Database URL: containers-us-west-123.railway.app:5432/railway
Database initialized successfully
Data directory: /app/data
Found 3 profile files
Migrated profile for user user123
Migrated profile for user user456
Found 2 draft files
Migrated 15 drafts for user user123
Migrated 8 drafts for user user456
============================================================
Migration Summary:
  - Profiles migrated: 3
  - Drafts migrated: 23
============================================================
Migration completed successfully!
```

---

## 🧪 Testing the Database

### Test 1: Create a User Profile

```bash
curl -X POST https://your-backend.railway.app/api/v1/users/profile \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "name": "Test User",
    "email": "test@example.com",
    "company": "ACME Corp",
    "role": "Manager"
  }'
```

### Test 2: Verify OAuth Flow

1. Sign in with Google via frontend
2. Check Railway logs for:
   ```
   Saved profile to database for user <google_user_id>
   ```

### Test 3: Generate an Email

1. Use the frontend to generate an email
2. Check Railway logs for:
   ```
   Saved draft to database for user <user_id>
   ```

### Test 4: Restart App and Verify Persistence

1. Trigger redeploy in Railway (or push a commit)
2. After restart, profiles and drafts should still exist
3. Check history in frontend - should show previous drafts

---

## 🔍 Database Management

### Access PostgreSQL Database

#### Option A: Railway Web Console

1. Go to PostgreSQL service in Railway
2. Click **Data** tab
3. Query tables directly in browser

#### Option B: psql CLI via Railway

```bash
railway connect postgresql
```

Then run SQL queries:
```sql
-- List all tables
\dt

-- Count user profiles
SELECT COUNT(*) FROM user_profiles;

-- Count drafts
SELECT COUNT(*) FROM drafts;

-- View recent drafts
SELECT id, user_id, created_at, LEFT(content, 50) as preview
FROM drafts
ORDER BY created_at DESC
LIMIT 10;
```

#### Option C: External Tool (DBeaver, pgAdmin, etc.)

Use the connection details from Railway:
- Host: From `PGHOST` variable
- Port: From `PGPORT` variable (usually 5432)
- Database: From `PGDATABASE` variable
- Username: From `PGUSER` variable
- Password: From `PGPASSWORD` variable

---

## 🧹 Maintenance

### Backup Data

Railway automatically backs up your database. To create manual backup:

1. Go to PostgreSQL service → **Backups** tab
2. Click **Create Backup**

### View Storage Usage

1. PostgreSQL service → **Metrics** tab
2. Check disk usage vs 5GB free tier limit

### Clean Old Drafts

To remove drafts older than 90 days:

```sql
DELETE FROM drafts
WHERE created_at < NOW() - INTERVAL '90 days';
```

---

## 🐛 Troubleshooting

### Issue: App Still Using JSON Files

**Symptoms:** No database logs, drafts lost on restart

**Solutions:**
1. Verify `DATABASE_URL` exists in app's environment variables
2. Check Railway logs for "DATABASE_URL not configured" message
3. Restart deployment after adding DATABASE_URL

### Issue: "relation 'user_profiles' does not exist"

**Symptoms:** Database connection works but tables missing

**Solutions:**
1. Check startup logs for "Creating database tables..."
2. Manually create tables via Railway CLI:
   ```bash
   railway run python -c "from src.db.database import init_db; init_db()"
   ```

### Issue: Migration Script Fails

**Symptoms:** `RuntimeError: Database not initialized`

**Solutions:**
1. Ensure DATABASE_URL is set in .env
2. Run migration from project root directory
3. Check PostgreSQL is running and accessible

### Issue: Duplicate Key Errors

**Symptoms:** `duplicate key value violates unique constraint`

**Solutions:**
- Migration script is idempotent - safe to re-run
- If re-running after partial migration, it skips existing records

---

## 🚀 Next Steps

### Add ChromaDB for Semantic Search (Optional)

PostgreSQL handles structured data (profiles, drafts). Add ChromaDB later for:
- Semantic search: "Find emails about project proposals"
- Similar draft discovery: "Show me emails with this tone"
- Context retrieval for AI prompts

ChromaDB and PostgreSQL work together:
- PostgreSQL stores the actual draft text and metadata
- ChromaDB stores embeddings and enables semantic search
- Both reference the same `draft.id` for lookups

See `CHROMADB_SETUP.md` (coming soon) for ChromaDB integration.

### Monitor Performance

Use Railway's built-in metrics:
1. PostgreSQL service → **Metrics**
2. Watch:
   - Query performance
   - Connection pool usage
   - Disk space trends

### Upgrade to Paid Tier (When Needed)

Free tier limits:
- 5GB storage
- 100GB bandwidth/month
- Shared CPU

Upgrade when you hit limits or need:
- More storage
- Dedicated resources
- Priority support

---

## 📚 Resources

- [Railway PostgreSQL Docs](https://docs.railway.app/databases/postgresql)
- [SQLAlchemy ORM Docs](https://docs.sqlalchemy.org/en/20/)
- [PostgreSQL Best Practices](https://www.postgresql.org/docs/current/tutorial.html)

---

## ✅ Checklist

- [ ] PostgreSQL service added to Railway project
- [ ] `DATABASE_URL` variable visible in app service
- [ ] App redeployed with database support
- [ ] Startup logs show "Database initialized successfully"
- [ ] Migration script run (if existing data)
- [ ] OAuth flow tested and profile saved
- [ ] Email generation tested and draft saved
- [ ] Drafts persist after app restart
- [ ] Database accessible via Railway console or psql

---

**Questions?** Check Railway logs first, then review this guide. PostgreSQL setup is one-time - once configured, it's "set and forget"! 🎉

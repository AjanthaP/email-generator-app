# Frontend Sync Guide

This guide explains how to sync the `frontend/` folder from this monorepo to the separate `email-generator-app-frontend` repository.

## ✅ Setup Complete

The repositories are now connected! The `frontend-repo` remote has been added and initial sync is complete.

## Quick Sync (After Making Frontend Changes)

### Method 1: PowerShell Script (Recommended)

```powershell
# Run the sync script from repo root
.\sync-frontend.ps1

# If push is rejected (history diverged), force push:
.\sync-frontend.ps1 -Force
```

### Method 2: Manual Git Subtree Commands

```powershell
# 1. Split the frontend folder
git subtree split --prefix=frontend -b frontend-split

# 2. Push to frontend repo
git push frontend-repo frontend-split:main

# 3. Clean up temporary branch
git branch -D frontend-split
```

## Workflow

### Daily Development Flow

```powershell
# 1. Make changes in frontend/ folder
cd frontend
# ... edit files ...

# 2. Commit to monorepo
git add .
git commit -m "Your change description"
git push origin master

# 3. Sync to frontend repo
cd ..
.\sync-frontend.ps1
```

### What Gets Synced

✅ **Synced:**
- All files in `frontend/` folder
- Full git history for frontend files
- Changes maintain commit messages

❌ **Not Synced:**
- `node_modules/` (excluded)
- `dist/` build output (excluded)
- Backend code (`src/`, `tests/`, etc.)

## Repository Structure

```
email-generator-app/ (monorepo - master branch)
├── frontend/          → Syncs to → email-generator-app-frontend (main branch)
├── src/               (backend - Python/FastAPI)
├── tests/
└── ...

email-generator-app-frontend/ (separate repo - main branch)
├── src/
├── public/
├── index.html
├── package.json
└── ...                (mirrors frontend/ folder)
```

## Vercel Deployment

The `email-generator-app-frontend` repository is connected to Vercel:
- **Auto-deploys** when you push to `main` branch
- After running `.\sync-frontend.ps1`, Vercel will deploy automatically
- Check deployment status at: https://vercel.com/dashboard

## Recent Changes Synced

✅ Latest sync (just completed):
- Updated app title to "AI powered Email Generator" (index.html)
- All previous frontend commits with full history

## Troubleshooting

### "Push rejected" error

If you get a rejection when syncing:

```powershell
# Force push to override frontend repo
.\sync-frontend.ps1 -Force
```

### "Remote frontend-repo not found"

The script will automatically add it, but you can manually add:

```powershell
git remote add frontend-repo https://github.com/AjanthaP/email-generator-app-frontend.git
git fetch frontend-repo
```

### Verify sync status

```powershell
# Check what's in frontend repo
git log frontend-repo/main --oneline -10

# Compare with monorepo frontend folder
git log --oneline -10 -- frontend/
```

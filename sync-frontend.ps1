#!/usr/bin/env pwsh
# Sync frontend folder to email-generator-app-frontend repository
# This uses git subtree to maintain history and sync changes

param(
    [switch]$Force = $false
)

Write-Host "=== Frontend Sync Script ===" -ForegroundColor Cyan
Write-Host ""

# Ensure we're in the repo root
$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
    Write-Host "Error: Not in a git repository" -ForegroundColor Red
    exit 1
}

Set-Location $repoRoot

# Check if frontend-repo remote exists
$remotes = git remote
if ($remotes -notcontains "frontend-repo") {
    Write-Host "Adding frontend-repo remote..." -ForegroundColor Yellow
    git remote add frontend-repo https://github.com/AjanthaP/email-generator-app-frontend.git
    git fetch frontend-repo
}

Write-Host "Syncing frontend/ folder to email-generator-app-frontend repo..." -ForegroundColor Green
Write-Host ""

# Split the frontend folder into a temporary branch
Write-Host "Splitting frontend folder..." -ForegroundColor Cyan
$splitResult = git subtree split --prefix=frontend -b frontend-split 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error splitting frontend folder" -ForegroundColor Red
    Write-Host $splitResult
    exit 1
}

Write-Host "Split complete!" -ForegroundColor Green
Write-Host ""

# Push to frontend repo
Write-Host "Pushing to frontend repository..." -ForegroundColor Cyan
if ($Force) {
    git push frontend-repo frontend-split:main --force
} else {
    git push frontend-repo frontend-split:main
}

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Push failed. If you need to force push, run:" -ForegroundColor Yellow
    Write-Host "  .\sync-frontend.ps1 -Force" -ForegroundColor Gray
    git branch -D frontend-split 2>$null
    exit 1
}

Write-Host "Push successful!" -ForegroundColor Green
Write-Host ""

# Clean up temporary branch
Write-Host "Cleaning up..." -ForegroundColor Cyan
git branch -D frontend-split 2>$null

Write-Host ""
Write-Host "=== Sync Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend changes have been pushed to:" -ForegroundColor Cyan
Write-Host "  https://github.com/AjanthaP/email-generator-app-frontend" -ForegroundColor Gray
Write-Host ""
Write-Host "Vercel will auto-deploy the changes shortly." -ForegroundColor Green

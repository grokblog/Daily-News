# Multi-Cloud Deployment Guide

This blog is configured for automated daily generation via **GitHub Actions** and seamless deployment to **Vercel, Netlify, or Cloudflare Pages**.

## 1. Setup GitHub Repository

1.  Create a **New Repository** on GitHub.
2.  Push your code:
    ```bash
    git init
    git add .
    git commit -m "Initial commit"
    git branch -M main
    git remote add origin https://github.com/USERNAME/REPO_NAME.git
    git push -u origin main
    ```

## 2. Configure GitHub Secrets (CRITICAL for Automation)

Since GitHub runs in the cloud, it cannot access your local Grok gateway (`localhost`). You MUST provide a real API Key.

1.  Go to your GitHub Repo -> **Settings**.
2.  Go to **Secrets and variables** -> **Actions**.
3.  Click **New repository secret**.
4.  Add `GROK_API_KEY`:
    - Value: Your **Real** API Key (e.g., `xai-....` or `sk-...`).
    - *Note: If using OpenAI instead of Grok, update `.github/workflows/generate_content.yml` URL.*

## 3. Deploy to Hosting

Choose one platform. They all connect to your GitHub repo.

### Option A: Vercel (Recommended)
1.  Go to [vercel.com/new](https://vercel.com/new).
2.  Import your GitHub repository.
3.  **Build & Output Settings**:
    - **Output Directory**: `public` (Override if needed).
    - **Build Command**: Leave empty (or `python build_site.py` if you want Vercel to rebuild).
4.  Click **Deploy**.

### Option B: Netlify
1.  Go to [app.netlify.com](https://app.netlify.com).
2.  "Add new site" -> "Import an existing project".
3.  Connect to GitHub.
4.  **Basic Build Settings**:
    - **Base directory**: `/`
    - **Build command**: `echo 'Pre-built'` (Since GitHub Actions handles generation).
    - **Publish directory**: `public`
5.  Click **Deploy site**.

### Option C: Cloudflare Pages
1.  Go to Cloudflare Dashboard -> **Pages**.
2.  Connect to Git.
3.  **Build settings**:
    - **Build command**: `exit 0` (Skip build).
    - **Build output directory**: `public`
4.  Click **Save and Deploy**.

## How It Works

1.  Every day at **06:00 UTC**, GitHub Actions runs.
2.  It generates new articles using your API Key.
3.  It builds the static site into `public/`.
4.  It **commits and pushes** the new content back to your repo.
5.  Vercel/Netlify detects the new commit and automatically updates your live site.

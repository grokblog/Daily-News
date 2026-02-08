---
description: Setup Auto-Generate Blog Content System
---

# Setup Auto-Generate Blog Content System

This workflow sets up the complete blog generation system with Grok AI integration.

## Steps

1. Install Python dependencies
```bash
pip install -r requirements.txt
```

2. Configure environment variables
- Copy `.env.example` to `.env`
- Add your Grok API credentials
- Set Google News RSS feed URLs

3. Test blog generation locally
```bash
python blog_generator.py --test
```

4. Build static site
```bash
python build_site.py
```

5. Deploy to GitHub Pages/Netlify/Vercel
- Push to GitHub
- Configure deployment settings
- Set up GitHub Actions for automated content generation

## Requirements
- Python 3.10+
- Grok API access
- GitHub account for deployment

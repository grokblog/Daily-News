# ✅ Setup Checklist - Grok Blog Generator

Gunakan checklist ini untuk memastikan semua langkah setup sudah dilakukan dengan benar.

---

## 📋 Pre-Setup Checklist

### Persyaratan Sistem
- [ ] Windows 10/11, macOS, atau Linux
- [ ] Python 3.10+ terinstall
- [ ] Git terinstall
- [ ] GitHub account (untuk deployment)
- [ ] Text editor (VS Code, Notepad++, dll)
- [ ] 2GB RAM minimum
- [ ] 1GB disk space

### Akses & Credentials
- [ ] Grok API Gateway sudah running
- [ ] Punya Grok API key
- [ ] GitHub account aktif
- [ ] (Optional) Custom domain

---

## 🚀 Installation Checklist

### 1. Clone & Setup Environment
- [ ] Clone repository
  ```bash
  git clone <your-repo>
  cd grok-blog
  ```
- [ ] Create virtual environment
  ```bash
  python -m venv venv
  ```
- [ ] Activate virtual environment
  - [ ] Windows: `venv\Scripts\activate`
  - [ ] macOS/Linux: `source venv/bin/activate`
- [ ] Install dependencies
  ```bash
  pip install -r requirements.txt
  ```

### 2. Configuration
- [ ] Copy `.env.example` to `.env`
  ```bash
  cp .env.example .env
  ```
- [ ] Edit `.env` file:
  - [ ] Set `GROK_API_KEY`
  - [ ] Set `GROK_API_URL`
  - [ ] Set `SITE_URL`
  - [ ] (Optional) Set `CUSTOM_DOMAIN`

### 3. Grok API Setup
- [ ] Start Grok API Gateway
  ```bash
  cd app
  python main.py
  ```
- [ ] Verify API running at `http://localhost:8017`
- [ ] Login to admin panel: `http://localhost:8017/login`
  - [ ] Username: `admin`
  - [ ] Password: `admin`
- [ ] Add Grok token
- [ ] Copy API key yang di-generate

### 4. Test Generation
- [ ] Generate test article
  ```bash
  python blog_generator.py --test
  ```
- [ ] Check output:
  - [ ] Article saved in `data/posts/*.json`
  - [ ] Image saved in `data/images/*.jpg`
  - [ ] No errors in console

### 5. Build & Preview
- [ ] Build static site
  ```bash
  python build_site.py
  ```
- [ ] Check output:
  - [ ] `public/index.html` exists
  - [ ] `public/posts/*.html` exists
  - [ ] `public/sitemap.xml` exists
  - [ ] `public/feed.xml` exists
  - [ ] `public/assets/` copied
- [ ] Preview locally
  ```bash
  cd public
  python -m http.server 8000
  ```
- [ ] Open browser: `http://localhost:8000`
- [ ] Verify:
  - [ ] Homepage loads correctly
  - [ ] Article page loads
  - [ ] Dark/light theme toggle works
  - [ ] Mobile responsive
  - [ ] No console errors

---

## 🔄 GitHub Setup Checklist

### 1. Repository Setup
- [ ] Create new GitHub repository
- [ ] Initialize git (if not already)
  ```bash
  git init
  git add .
  git commit -m "Initial commit: Grok Blog Generator"
  ```
- [ ] Add remote
  ```bash
  git remote add origin https://github.com/username/repo.git
  ```
- [ ] Push to GitHub
  ```bash
  git push -u origin main
  ```

### 2. GitHub Secrets
- [ ] Go to repository Settings → Secrets and variables → Actions
- [ ] Add secrets:
  - [ ] `GROK_API_KEY` = your Grok API key
  - [ ] `GROK_API_URL` = your Grok API URL (jika hosted)
  - [ ] `SITE_URL` = your site URL
  - [ ] (Optional) `CUSTOM_DOMAIN` = your custom domain

### 3. GitHub Pages
- [ ] Go to Settings → Pages
- [ ] Source: Deploy from a branch
- [ ] Branch: `gh-pages`
- [ ] Save
- [ ] Wait for first deployment (via Actions)

### 4. GitHub Actions
- [ ] Go to Actions tab
- [ ] Verify workflow exists: "Auto Generate Blog Content"
- [ ] (Optional) Run workflow manually:
  - [ ] Click "Run workflow"
  - [ ] Set article count (default: 5)
  - [ ] Click "Run workflow"
- [ ] Wait for completion
- [ ] Check workflow logs for errors
- [ ] Verify deployment success

---

## 🌐 Deployment Checklist

### GitHub Pages
- [ ] Site accessible at: `https://username.github.io/repo`
- [ ] (Optional) Custom domain configured
  - [ ] Add CNAME file to `public/`
  - [ ] Configure DNS:
    - [ ] CNAME record: `blog` → `username.github.io`
  - [ ] Wait for DNS propagation (up to 24 hours)
  - [ ] Verify custom domain works

### Alternative Platforms

#### Netlify
- [ ] Install Netlify CLI: `npm install -g netlify-cli`
- [ ] Login: `netlify login`
- [ ] Deploy: `netlify deploy --dir=public --prod`
- [ ] Or connect via Netlify UI:
  - [ ] Import GitHub repository
  - [ ] Build command: `python build_site.py`
  - [ ] Publish directory: `public`
  - [ ] Deploy

#### Vercel
- [ ] Install Vercel CLI: `npm install -g vercel`
- [ ] Deploy: `vercel --prod`
- [ ] Or connect via Vercel UI:
  - [ ] Import GitHub repository
  - [ ] Framework: Other
  - [ ] Build command: `python build_site.py`
  - [ ] Output directory: `public`
  - [ ] Deploy

#### Cloudflare Pages
- [ ] Login to Cloudflare Dashboard
- [ ] Pages → Create a project
- [ ] Connect GitHub repository
- [ ] Build settings:
  - [ ] Build command: `python build_site.py`
  - [ ] Build output: `public`
- [ ] Environment variables: Add secrets
- [ ] Deploy

---

## 🎨 Customization Checklist

### Basic Customization
- [ ] Edit site name in `blog_config.py`
- [ ] Edit site description in `blog_config.py`
- [ ] Change theme colors in `templates/assets/css/main.css`
- [ ] Update logo/favicon
- [ ] Add author avatar image

### Advanced Customization
- [ ] Add/remove categories in `blog_config.py`
- [ ] Customize AI prompts in `blog_config.py`
- [ ] Modify templates:
  - [ ] `templates/article.html`
  - [ ] `templates/index.html`
  - [ ] `templates/category.html`
- [ ] Add custom pages
- [ ] Integrate analytics (Google Analytics, etc)
- [ ] Add comment system (Disqus, etc)

---

## 📊 SEO Checklist

### On-Site SEO
- [ ] Submit sitemap to Google Search Console
  - [ ] Go to: https://search.google.com/search-console
  - [ ] Add property: your site URL
  - [ ] Submit sitemap: `https://yoursite.com/sitemap.xml`
- [ ] Verify meta tags:
  - [ ] Title tags (50-60 chars)
  - [ ] Meta descriptions (150-160 chars)
  - [ ] Keywords
  - [ ] Open Graph tags
  - [ ] Twitter Cards
- [ ] Check schema markup:
  - [ ] Test with: https://search.google.com/test/rich-results
  - [ ] Verify NewsArticle schema
  - [ ] Verify Organization schema
- [ ] Mobile-friendly test:
  - [ ] Test with: https://search.google.com/test/mobile-friendly
- [ ] Page speed test:
  - [ ] Test with: https://pagespeed.web.dev/

### Off-Site SEO
- [ ] Share articles on social media
- [ ] Build backlinks
- [ ] Submit to directories
- [ ] Guest posting
- [ ] Social bookmarking

---

## 🔧 Maintenance Checklist

### Daily
- [ ] Check GitHub Actions logs
- [ ] Verify new articles generated
- [ ] Monitor site uptime

### Weekly
- [ ] Review generated content quality
- [ ] Check for errors/issues
- [ ] Update categories if needed
- [ ] Analyze traffic (Google Analytics)

### Monthly
- [ ] Review SEO performance
- [ ] Update dependencies
  ```bash
  pip install --upgrade -r requirements.txt
  ```
- [ ] Backup data
- [ ] Clean cache if needed
  ```bash
  rm -rf .cache/
  ```

---

## 🐛 Troubleshooting Checklist

### If Content Generation Fails
- [ ] Check Grok API is running
- [ ] Verify API key is correct
- [ ] Check internet connection
- [ ] Review error logs
- [ ] Clear cache: `rm -rf .cache/`
- [ ] Try test mode: `python blog_generator.py --test`

### If Build Fails
- [ ] Verify articles exist in `data/posts/`
- [ ] Check template syntax
- [ ] Review build logs
- [ ] Test locally first

### If Deployment Fails
- [ ] Check GitHub Secrets are set
- [ ] Verify workflow file syntax
- [ ] Review Actions logs
- [ ] Check branch permissions

### If Site Not Loading
- [ ] Verify GitHub Pages is enabled
- [ ] Check DNS settings (if custom domain)
- [ ] Wait for DNS propagation
- [ ] Clear browser cache
- [ ] Check for 404 errors

---

## ✅ Final Verification

### Functionality
- [ ] Homepage loads
- [ ] Articles load
- [ ] Categories work
- [ ] Search engines can crawl
- [ ] RSS feed works
- [ ] Sitemap accessible
- [ ] Mobile responsive
- [ ] Dark/light theme works
- [ ] Social sharing works
- [ ] Images load correctly

### Performance
- [ ] Page load time < 3 seconds
- [ ] Images optimized
- [ ] CSS/JS minified
- [ ] No console errors
- [ ] No broken links

### SEO
- [ ] Meta tags present
- [ ] Schema markup valid
- [ ] Sitemap submitted
- [ ] Google Search Console verified
- [ ] Analytics tracking

### Automation
- [ ] GitHub Actions running
- [ ] Cronjob working (check after 6 hours)
- [ ] Auto-deployment working
- [ ] No workflow errors

---

## 🎉 Launch Checklist

### Pre-Launch
- [ ] All above checklists completed
- [ ] Content quality reviewed
- [ ] Site tested on multiple devices
- [ ] SEO optimized
- [ ] Analytics setup

### Launch
- [ ] Announce on social media
- [ ] Share with friends/community
- [ ] Submit to search engines
- [ ] Monitor initial traffic
- [ ] Respond to feedback

### Post-Launch
- [ ] Monitor analytics daily
- [ ] Fix any issues quickly
- [ ] Continue content generation
- [ ] Build audience
- [ ] Monetize (AdSense, etc)

---

## 📞 Need Help?

Jika ada yang tidak jelas atau mengalami masalah:

1. **Check Documentation**
   - [ ] [README-ID.md](README-ID.md) - Dokumentasi lengkap
   - [ ] [PROJECT-SUMMARY.md](PROJECT-SUMMARY.md) - Quick reference
   - [ ] [WORKFLOW-DIAGRAM.md](WORKFLOW-DIAGRAM.md) - Visual guide

2. **Troubleshooting**
   - [ ] Review error messages
   - [ ] Check logs
   - [ ] Search GitHub Issues

3. **Get Support**
   - [ ] GitHub Issues
   - [ ] GitHub Discussions
   - [ ] Email support

---

<div align="center">

**Setup Checklist Complete! 🎉**

*Selamat! Blog Anda siap untuk auto-generate konten berkualitas tinggi!*

**Happy Blogging! 🚀**

</div>

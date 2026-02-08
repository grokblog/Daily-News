# 🚀 Auto-Generate Blog Content with Grok AI

> **Sistem otomatis untuk generate konten blog berkualitas tinggi dari Google News menggunakan Grok AI**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)
[![Grok AI](https://img.shields.io/badge/Powered%20by-Grok%20AI-orange.svg)](https://x.ai)

---

## 🌟 Fitur Utama

### ✨ Content Generation
- 🤖 **Auto-rewrite** artikel dari Google News RSS dengan Grok AI
- 📝 **SEO-optimized** content dengan keyword density yang tepat
- 🎨 **Auto-generate images** menggunakan Grok AI
- 🏆 **High-quality content** (1500-3000 kata per artikel)
- 🔥 **Viral potential scoring** untuk prioritas konten

### 🎯 SEO & Schema
- ✅ **Rich Schema.org markup** (NewsArticle, BreadcrumbList, Organization)
- 🗺️ **Auto-generated sitemap.xml**
- 📡 **RSS Feed** untuk subscribers
- 🔗 **WordPress-style URLs** (slug-based)
- 📊 **Open Graph & Twitter Cards**

### 🎨 Design & Theme
- 💎 **Mediumish-inspired** modern design
- 🌓 **Dark/Light theme** toggle
- 📱 **Fully responsive** mobile-first design
- ⚡ **Fast loading** static HTML
- 🎭 **Premium aesthetics** dengan gradients & animations

### 🔄 Automation
- ⏰ **GitHub Actions cronjob** (setiap 6 jam)
- 🚀 **Auto-deploy** ke GitHub Pages/Netlify/Vercel/Cloudflare Pages
- 💾 **Smart caching** untuk avoid duplikasi
- 📈 **Scalable** architecture

### 📰 Content Sources
- 🇮🇩 **Google News Indonesia** RSS feeds
- 📂 **6 Kategori viral**: Teknologi, Bisnis, Hiburan, Olahraga, Kesehatan, Sains
- 🎯 **Auto-select** artikel dengan potensi viral tinggi

---

## 📦 Installation

### Prerequisites
- Python 3.10+
- Grok API access (dari aplikasi Grok API Gateway)
- GitHub account (untuk deployment)

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/grok-blog.git
cd grok-blog

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Edit .env dengan konfigurasi Anda
# GROK_API_KEY=your-api-key
# SITE_URL=https://yoursite.com
```

---

## ⚙️ Configuration

### 1. Setup Grok API

Pastikan Grok API Gateway sudah running (dari folder `app`):

```bash
# Di terminal terpisah, jalankan Grok API
cd app
python main.py
```

API akan running di `http://localhost:8017`

### 2. Configure Environment Variables

Edit file `.env`:

```env
GROK_API_URL=http://localhost:8017/v1/chat/completions
GROK_API_KEY=your-api-key-here
SITE_URL=https://yoursite.com
ARTICLES_PER_RUN=5
```

### 3. Customize Blog Settings

Edit `blog_config.py` untuk customize:
- Site name & description
- RSS feed URLs
- Content length
- Categories
- SEO settings

---

## 🚀 Usage

### Generate Content Locally

```bash
# Generate 5 artikel (default)
python blog_generator.py

# Generate custom jumlah
python blog_generator.py --count 10

# Test mode (1 artikel)
python blog_generator.py --test
```

### Build Static Site

```bash
# Build semua halaman HTML
python build_site.py
```

Output akan ada di folder `public/`:
- `index.html` - Homepage
- `posts/*.html` - Article pages
- `kategori/*.html` - Category pages
- `sitemap.xml` - Sitemap
- `feed.xml` - RSS feed

### Preview Locally

```bash
# Serve static files
cd public
python -m http.server 8000

# Buka browser: http://localhost:8000
```

---

## 🔄 Automated Deployment

### GitHub Actions Setup

1. **Push ke GitHub**:
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Setup Secrets** di GitHub repository settings:
   - `GROK_API_KEY` - Your Grok API key
   - `GROK_API_URL` - Grok API endpoint
   - `SITE_URL` - Your site URL
   - `CUSTOM_DOMAIN` - (Optional) Custom domain

3. **Enable GitHub Pages**:
   - Settings → Pages
   - Source: Deploy from branch
   - Branch: `gh-pages`

4. **Workflow akan auto-run**:
   - Setiap 6 jam (cron schedule)
   - Manual trigger via Actions tab
   - Auto-deploy ke GitHub Pages

### Deploy ke Platform Lain

#### Netlify
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --dir=public --prod
```

#### Vercel
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

#### Cloudflare Pages
1. Connect GitHub repository
2. Build command: `python build_site.py`
3. Output directory: `public`

---

## 📁 Project Structure

```
grok-blog/
├── .github/
│   └── workflows/
│       └── auto-generate.yml    # GitHub Actions workflow
├── templates/
│   ├── article.html             # Article template
│   ├── index.html               # Homepage template
│   ├── category.html            # Category template
│   └── assets/
│       ├── css/
│       │   ├── main.css         # Main styles
│       │   └── home.css         # Homepage styles
│       └── js/
│           └── main.js          # JavaScript
├── public/                      # Generated static site (output)
├── data/
│   └── posts/                   # Generated articles (JSON)
├── .cache/                      # Cache untuk processed articles
├── blog_config.py               # Configuration
├── blog_generator.py            # Main generator
├── grok_client.py               # Grok API client
├── rss_parser.py                # RSS feed parser
├── build_site.py                # Static site builder
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

---

## 🎨 Customization

### Theme Colors

Edit `templates/assets/css/main.css`:

```css
:root {
    --color-primary: #0066FF;      /* Primary color */
    --color-secondary: #FF6B6B;    /* Secondary color */
    --color-accent: #4ECDC4;       /* Accent color */
}
```

### Content Prompts

Edit `blog_config.py` untuk customize prompts:
- `CONTENT_REWRITE_PROMPT` - Content generation
- `IMAGE_GENERATION_PROMPT` - Image generation
- `SEO_SCHEMA_TEMPLATE` - Schema markup

### Categories

Tambah/edit kategori di `blog_config.py`:

```python
GOOGLE_NEWS_FEEDS = {
    "kategori-baru": "https://news.google.com/rss/...",
}
```

---

## 📊 Content Quality

### SEO Optimization
- ✅ Unique content (100% rewritten)
- ✅ Keyword density 2-3%
- ✅ Meta description 150-160 chars
- ✅ Title 50-60 chars
- ✅ H2/H3 headings structure
- ✅ Internal linking
- ✅ Image alt texts

### Content Structure
- 📝 Engaging intro paragraph
- 📑 3-5 main sections (H2)
- 📌 2-3 subsections per section (H3)
- 📊 Bullet points for readability
- 🎯 Clear conclusion/CTA

### Quality Metrics
- 📏 1500-3000 words per article
- 📖 200 words/minute reading time
- 🎯 Viral potential scoring
- ✨ Grammar & spelling check

---

## 🔧 Troubleshooting

### Common Issues

**1. Grok API Error**
```
Error: Failed to connect to Grok API
```
**Solution**: Pastikan Grok API Gateway running di `http://localhost:8017`

**2. No Articles Generated**
```
Warning: No new articles found
```
**Solution**: 
- Check RSS feeds masih aktif
- Clear cache: `rm -rf .cache/`
- Coba manual: `python blog_generator.py --test`

**3. Image Generation Failed**
```
Error: Image generation failed
```
**Solution**: 
- Check Grok API quota
- Set `ENABLE_IMAGE_GENERATION=False` di config untuk skip images

**4. Build Failed**
```
Error: No articles found
```
**Solution**: Generate articles dulu dengan `python blog_generator.py`

---

## 📈 Performance

### Optimization Tips

1. **Enable Caching**:
```python
ENABLE_CACHE = True
CACHE_EXPIRY_HOURS = 24
```

2. **Optimize Images**:
- Auto-compress to JPEG quality 85
- Lazy loading enabled
- Responsive images

3. **Static Site Benefits**:
- ⚡ Lightning fast loading
- 💰 Zero hosting cost (GitHub Pages)
- 🔒 Secure (no backend)
- 📈 SEO-friendly

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## ⚠️ Disclaimer

- **Educational Purpose**: Project ini untuk pembelajaran dan research
- **Content Rights**: Pastikan comply dengan terms of service Google News
- **API Usage**: Gunakan Grok API sesuai quota dan terms
- **Responsibility**: User bertanggung jawab atas konten yang di-generate

---

## 🙏 Acknowledgments

- [Grok AI](https://x.ai) - AI content generation
- [Google News](https://news.google.com) - News sources
- [Mediumish Theme](https://www.wowthemes.net/mediumish-free-jekyll-template/) - Design inspiration

---

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/grok-blog/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/grok-blog/discussions)
- 📧 **Email**: your.email@example.com

---

## 🎯 Roadmap

- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Social media auto-posting
- [ ] Email newsletter integration
- [ ] Comment system
- [ ] Search functionality
- [ ] AMP pages support
- [ ] PWA features

---

<div align="center">

**Made with ❤️ using Grok AI**

[⭐ Star this repo](https://github.com/yourusername/grok-blog) if you find it useful!

</div>

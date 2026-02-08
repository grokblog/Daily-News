# 🚀 Auto-Generate Blog Content dengan Grok AI

<div align="center">

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)
[![Grok AI](https://img.shields.io/badge/Powered%20by-Grok%20AI-orange.svg)](https://x.ai)

- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)

---

## 🌟 Fitur Utama

### ✨ Generasi Konten Otomatis
- 🤖 **Auto-rewrite** artikel dari Google News RSS menggunakan Grok AI
- 📝 **SEO-optimized** dengan keyword density yang tepat (2-3%)
- 🎨 **Auto-generate gambar** featured image menggunakan Grok AI
- 🏆 **Konten berkualitas tinggi** (1500-3000 kata per artikel)
- 🔥 **Viral potential scoring** untuk prioritas konten

### 🎯 SEO & Schema Markup
- ✅ **Rich Schema.org markup** (NewsArticle, BreadcrumbList, Organization)
- 🗺️ **Sitemap.xml otomatis** untuk Google Search Console
- 📡 **RSS Feed** untuk subscribers
- 🔗 **WordPress-style URLs** (slug langsung ke URL)
- 📊 **Open Graph & Twitter Cards** untuk social media

### 🎨 Design & Theme Premium
- 💎 **Mediumish-inspired** design yang modern dan elegan
- 🌓 **Dark/Light theme** toggle dengan smooth transition
- 📱 **Fully responsive** mobile-first design
- ⚡ **Fast loading** static HTML (no database, no backend)
- 🎭 **Premium aesthetics** dengan gradients, shadows, dan animations

### 🔄 Automation & Deployment
- ⏰ **GitHub Actions cronjob** (auto-run setiap 6 jam)
- 🚀 **Auto-deploy** ke GitHub Pages/Netlify/Vercel/Cloudflare Pages
- 💾 **Smart caching** untuk hindari duplikasi artikel
- 📈 **Scalable** architecture

### 📰 Sumber Konten
- 🇮🇩 **Google News Indonesia** RSS feeds
- 📂 **6 Kategori viral**: Teknologi, Bisnis, Hiburan, Olahraga, Kesehatan, Sains
- 🎯 **Auto-select** artikel dengan potensi viral tinggi

---

## 📦 Instalasi

### Persyaratan Sistem
- Windows 10/11, macOS, atau Linux
- Python 3.10 atau lebih baru
- Akses ke Grok API (dari aplikasi Grok API Gateway yang sudah ada)
- GitHub account (untuk deployment otomatis)
- 2GB RAM minimum
- 1GB disk space

### Langkah Instalasi

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/grok-blog.git
cd grok-blog
```

#### 2. Setup Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Setup Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env dengan editor favorit Anda
notepad .env  # Windows
nano .env     # Linux/macOS
```

Isi dengan konfigurasi Anda:
```env
GROK_API_URL=http://localhost:8017/v1/chat/completions
GROK_API_KEY=your-api-key-here
SITE_URL=https://yoursite.com
```

---

## ⚙️ Konfigurasi

### 1. Setup Grok API Gateway

Pastikan Grok API Gateway sudah running:

```bash
# Buka terminal baru
cd app
python main.py
```

API akan berjalan di `http://localhost:8017`

Untuk mendapatkan API key:
1. Buka browser: `http://localhost:8017/login`
2. Login dengan username: `admin`, password: `admin`
3. Tambahkan token Grok Anda
4. Copy API key yang di-generate

### 2. Konfigurasi Blog

Edit `blog_config.py` untuk customize:

```python
# Site Information
SITE_NAME = "Viral News Hub"
SITE_DESCRIPTION = "Berita Terkini & Viral"
SITE_URL = "https://yoursite.com"

# Content Settings
ARTICLES_PER_RUN = 5  # Jumlah artikel per run
MIN_CONTENT_LENGTH = 1500  # Minimum kata
MAX_CONTENT_LENGTH = 3000  # Maximum kata

# Google News RSS Feeds
GOOGLE_NEWS_FEEDS = {
    "teknologi": "https://news.google.com/rss/...",
    "bisnis": "https://news.google.com/rss/...",
    # Tambah kategori lain...
}
```

### 3. Customize Theme

Edit warna di `templates/assets/css/main.css`:

```css
:root {
    --color-primary: #0066FF;      /* Warna utama */
    --color-secondary: #FF6B6B;    /* Warna sekunder */
    --color-accent: #4ECDC4;       /* Warna aksen */
}
```

---

## 🚀 Cara Penggunaan

### Quick Start (Windows)

Jalankan script otomatis:
```bash
start.bat
```

Menu akan muncul dengan pilihan:
1. Generate test (1 artikel)
2. Generate 5 artikel
3. Build static site
4. Generate + Build
5. Start local server

### Manual Usage

#### Generate Konten

```bash
# Generate 5 artikel (default)
python blog_generator.py

# Generate custom jumlah
python blog_generator.py --count 10

# Test mode (1 artikel saja)
python blog_generator.py --test
```

Output:
- Artikel disimpan di `data/posts/*.json`
- Gambar disimpan di `data/images/*.jpg`

#### Build Static Site

```bash
python build_site.py
```

Output di folder `public/`:
```
public/
├── index.html              # Homepage
├── posts/
│   ├── artikel-1.html
│   ├── artikel-2.html
│   └── ...
├── kategori/
│   ├── teknologi.html
│   ├── bisnis.html
│   └── ...
├── sitemap.xml             # Sitemap
├── feed.xml                # RSS Feed
├── assets/
│   ├── css/
│   ├── js/
│   └── images/
└── images/                 # Featured images
```

#### Preview Locally

```bash
cd public
python -m http.server 8000

# Buka browser: http://localhost:8000
```

---

## 🔄 Deployment Otomatis

### Setup GitHub Actions

#### 1. Push ke GitHub

```bash
git add .
git commit -m "Initial commit: Grok Blog Generator"
git push origin main
```

#### 2. Setup GitHub Secrets

Buka repository settings → Secrets and variables → Actions

Tambahkan secrets berikut:

| Secret Name | Value | Deskripsi |
|------------|-------|-----------|
| `GROK_API_KEY` | `your-api-key` | API key dari Grok |
| `GROK_API_URL` | `http://your-api-url` | URL Grok API (jika hosted) |
| `SITE_URL` | `https://yoursite.com` | URL site Anda |
| `CUSTOM_DOMAIN` | `blog.yourdomain.com` | (Optional) Custom domain |

#### 3. Enable GitHub Pages

1. Settings → Pages
2. Source: Deploy from branch
3. Branch: `gh-pages`
4. Save

#### 4. Workflow Otomatis

Workflow akan auto-run:
- ⏰ **Setiap 6 jam** (cron: `0 */6 * * *`)
- 🖱️ **Manual trigger** via Actions tab
- 📝 **Auto-commit** generated content
- 🚀 **Auto-deploy** ke GitHub Pages

Untuk manual trigger:
1. Buka tab **Actions**
2. Pilih **Auto Generate Blog Content**
3. Click **Run workflow**
4. (Optional) Set jumlah artikel
5. Click **Run workflow**

### Deploy ke Platform Lain

#### Netlify

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy
netlify deploy --dir=public --prod
```

Atau via Netlify UI:
1. Connect GitHub repository
2. Build command: `python build_site.py`
3. Publish directory: `public`

#### Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

Atau via Vercel UI:
1. Import GitHub repository
2. Framework: Other
3. Build command: `python build_site.py`
4. Output directory: `public`

#### Cloudflare Pages

1. Login ke Cloudflare Dashboard
2. Pages → Create a project
3. Connect GitHub repository
4. Build settings:
   - Build command: `python build_site.py`
   - Build output: `public`
5. Environment variables: Add `GROK_API_KEY`, etc.

---

## 📁 Struktur Project

```
grok-blog/
├── .github/
│   └── workflows/
│       └── auto-generate.yml       # GitHub Actions workflow
│
├── templates/                      # HTML templates
│   ├── article.html                # Template artikel
│   ├── index.html                  # Template homepage
│   ├── category.html               # Template kategori
│   └── assets/
│       ├── css/
│       │   ├── main.css            # Styles utama
│       │   └── home.css            # Styles homepage
│       └── js/
│           └── main.js             # JavaScript
│
├── data/                           # Data folder
│   ├── posts/                      # Generated articles (JSON)
│   └── images/                     # Downloaded images
│
├── public/                         # Generated static site
│   ├── index.html
│   ├── posts/
│   ├── kategori/
│   ├── sitemap.xml
│   ├── feed.xml
│   └── assets/
│
├── .cache/                         # Cache folder
│   └── processed_articles.json    # Processed IDs
│
├── blog_config.py                  # Configuration
├── blog_generator.py               # Main generator
├── grok_client.py                  # Grok API client
├── rss_parser.py                   # RSS parser
├── build_site.py                   # Site builder
│
├── requirements.txt                # Dependencies
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore
├── start.bat                       # Quick start (Windows)
└── README.md                       # Documentation
```

---

## 🎨 Customization

### Mengubah Kategori

Edit `blog_config.py`:

```python
GOOGLE_NEWS_FEEDS = {
    "teknologi": "https://news.google.com/rss/topics/...",
    "kategori-baru": "https://news.google.com/rss/topics/...",
}
```

Untuk mendapatkan RSS feed URL:
1. Buka [Google News](https://news.google.com)
2. Pilih kategori/topik
3. Scroll ke bawah → "RSS"
4. Copy URL

### Mengubah Prompt AI

Edit `blog_config.py`:

```python
CONTENT_REWRITE_PROMPT = """
Tugas: Rewrite artikel dengan style Anda...

Requirements:
1. ...
2. ...
"""
```

### Mengubah Design

**Colors:**
Edit `templates/assets/css/main.css`

**Layout:**
Edit template files di `templates/`

**Fonts:**
Ganti di `<head>` section template:
```html
<link href="https://fonts.googleapis.com/css2?family=Your+Font&display=swap" rel="stylesheet">
```

### Menambah Halaman

1. Buat template di `templates/your-page.html`
2. Edit `build_site.py`:
```python
def build_your_page(self):
    template = self.jinja_env.get_template('your-page.html')
    html = template.render(...)
    # Save to public/
```

---

## 🔧 Troubleshooting

### Error: Grok API Connection Failed

**Penyebab:** Grok API tidak running atau URL salah

**Solusi:**
```bash
# Check Grok API status
curl http://localhost:8017/api/stats

# Restart Grok API
cd app
python main.py
```

### Error: No Articles Generated

**Penyebab:** RSS feed error atau semua artikel sudah diproses

**Solusi:**
```bash
# Clear cache
rm -rf .cache/

# Test dengan 1 artikel
python blog_generator.py --test

# Check RSS feeds
python rss_parser.py
```

### Error: Image Generation Failed

**Penyebab:** Grok API quota habis atau error

**Solusi:**
```python
# Disable image generation sementara
# Edit blog_config.py
ENABLE_IMAGE_GENERATION = False
```

### Error: Build Failed - No Articles

**Penyebab:** Belum generate artikel

**Solusi:**
```bash
# Generate artikel dulu
python blog_generator.py

# Baru build
python build_site.py
```

### GitHub Actions Failed

**Penyebab:** Secrets tidak di-set atau error di script

**Solusi:**
1. Check GitHub Secrets sudah benar
2. Check workflow logs di Actions tab
3. Test locally dulu sebelum push

---

## ❓ FAQ

### Q: Berapa lama waktu generate 1 artikel?

**A:** Sekitar 30-60 detik per artikel (tergantung Grok API response time)

### Q: Apakah bisa custom domain?

**A:** Ya! Set `CUSTOM_DOMAIN` secret di GitHub dan configure DNS:
```
CNAME record: blog → yourusername.github.io
```

### Q: Apakah konten 100% unique?

**A:** Ya, Grok AI me-rewrite dengan style berbeda. Tapi tetap check manual untuk quality assurance.

### Q: Berapa biaya hosting?

**A:** **GRATIS!** Jika pakai GitHub Pages, Netlify free tier, atau Cloudflare Pages.

### Q: Bisa pakai bahasa lain selain Indonesia?

**A:** Ya, edit `SITE_LANGUAGE` di config dan sesuaikan prompt di `blog_config.py`

### Q: Apakah SEO-friendly?

**A:** Sangat! Sudah include:
- Schema.org markup
- Sitemap.xml
- Meta tags lengkap
- Semantic HTML
- Fast loading (static)

### Q: Bisa monetize dengan AdSense?

**A:** Ya, tinggal tambahkan AdSense code di template HTML.

### Q: Apakah mobile-friendly?

**A:** Ya, fully responsive dengan mobile-first design.

---

## 📊 Performance Tips

### Optimasi Kecepatan

1. **Enable Caching:**
```python
ENABLE_CACHE = True
CACHE_EXPIRY_HOURS = 24
```

2. **Compress Images:**
Sudah auto-compress ke JPEG quality 85

3. **Lazy Loading:**
Sudah enabled untuk semua images

4. **CDN:**
Deploy ke Cloudflare Pages untuk global CDN

### SEO Best Practices

✅ **Sudah Implemented:**
- Unique titles & descriptions
- Schema.org markup
- Sitemap.xml
- RSS feed
- Semantic HTML
- Fast loading
- Mobile responsive

📝 **Recommendations:**
- Submit sitemap ke Google Search Console
- Enable Google Analytics
- Setup Search Console
- Build backlinks
- Share di social media

---

## 🤝 Contributing

Kontribusi sangat welcome! Silakan:

1. Fork repository
2. Create feature branch
```bash
git checkout -b feature/amazing-feature
```
3. Commit changes
```bash
git commit -m 'Add amazing feature'
```
4. Push to branch
```bash
git push origin feature/amazing-feature
```
5. Open Pull Request

---

## 📄 License

Project ini menggunakan MIT License - lihat file [LICENSE](LICENSE)

---

## ⚠️ Disclaimer

- **Tujuan Edukasi:** Project ini untuk pembelajaran dan research
- **Content Rights:** Pastikan comply dengan ToS Google News
- **API Usage:** Gunakan Grok API sesuai quota dan terms
- **Tanggung Jawab:** User bertanggung jawab atas konten yang di-generate
- **No Warranty:** Provided "as is" without warranty

---

## 🙏 Credits

- **Grok AI** - AI content generation
- **Google News** - News sources
- **Mediumish Theme** - Design inspiration
- **Community** - Contributors & supporters

---

## 📞 Support & Contact

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/yourusername/grok-blog/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/yourusername/grok-blog/discussions)
- 📧 **Email:** your.email@example.com
- 💬 **Telegram:** @yourusername

---

## 🎯 Roadmap

### v1.0 (Current)
- [x] Auto content generation
- [x] SEO optimization
- [x] Mediumish theme
- [x] GitHub Actions
- [x] Multi-platform deployment

### v1.1 (Planned)
- [ ] Multi-language support
- [ ] Advanced analytics
- [ ] Social auto-posting
- [ ] Email newsletter
- [ ] Comment system

### v2.0 (Future)
- [ ] Admin dashboard
- [ ] Content scheduling
- [ ] A/B testing
- [ ] Advanced SEO tools
- [ ] PWA support

---

<div align="center">

**Dibuat dengan ❤️ menggunakan Grok AI**

[⭐ Star Repository Ini](https://github.com/yourusername/grok-blog) jika bermanfaat!

**Happy Blogging! 🚀**

</div>

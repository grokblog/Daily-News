# 🔧 Setup Guide - Grok Blog Generator dengan SSO Cookies

## ⚠️ PENTING: Cara Kerja Sistem Ini

Sistem blog generator ini menggunakan **Grok API Gateway** yang sudah Anda buat, yang bekerja dengan **SSO cookies** (bukan API key biasa).

---

## 📋 Prerequisites

### 1. Grok API Gateway Harus Running

Pastikan Grok API Gateway sudah berjalan:

```bash
# Di terminal terpisah
cd c:\wank\IYAN\grok-blog
python main.py
```

Server akan running di: `http://localhost:8017`

### 2. Tambahkan Token Grok

Sebelum bisa generate content, Anda **HARUS** menambahkan token Grok ke API Gateway:

#### Cara 1: Via Admin Panel (Recommended)

1. **Buka browser**: `http://localhost:8017/login`
2. **Login**:
   - Username: `admin`
   - Password: `admin`
3. **Tambah Token**:
   - Klik "Add Tokens"
   - Masukkan token Grok Anda (dari cookies SSO)
   - Save

#### Cara 2: Via File (Manual)

Edit file `data/tokens.json` (jika ada) atau tambahkan via admin panel.

### 3. Verify Token Tersimpan

Cek di admin panel bahwa token sudah tersimpan dan aktif.

---

## 🚀 Cara Mendapatkan Token Grok (SSO Cookies)

### Method 1: Browser DevTools

1. **Login ke Grok.com** di browser
2. **Buka DevTools** (F12)
3. **Go to Application/Storage** → Cookies
4. **Copy cookies** yang diperlukan:
   - `auth_token` atau
   - `session_token` atau
   - Cookie lain yang digunakan untuk auth

### Method 2: Export dari Browser Extension

Gunakan extension seperti "EditThisCookie" atau "Cookie Editor" untuk export cookies.

---

## ✅ Verification Steps

### 1. Check Grok API Gateway Running

```bash
# Test health endpoint
curl http://localhost:8017/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Grok for Learning Only",
  "version": "1.0.3"
}
```

### 2. Check Token Available

Buka admin panel dan pastikan ada minimal 1 token aktif.

### 3. Test Blog Generator

```bash
python blog_generator.py --test
```

Jika berhasil, Anda akan melihat:
- ✅ RSS feeds parsed (237 articles found)
- ✅ Article generated
- ✅ Image downloaded
- ✅ JSON saved to `data/posts/`

---

## 🐛 Troubleshooting

### Error: "500 Server Error"

**Penyebab**: Tidak ada token Grok yang tersimpan di API Gateway

**Solusi**:
1. Pastikan Grok API Gateway running
2. Login ke admin panel: `http://localhost:8017/login`
3. Tambahkan token Grok
4. Verify token aktif
5. Test lagi: `python blog_generator.py --test`

### Error: "Connection refused"

**Penyebab**: Grok API Gateway tidak running

**Solusi**:
```bash
# Start API Gateway
python main.py
```

### Error: "No module named 'feedparser'"

**Penyebab**: Dependencies belum terinstall

**Solusi**:
```bash
pip install feedparser beautifulsoup4 lxml Pillow jinja2 python-dateutil
```

---

## 📝 Configuration File (.env)

File `.env` sudah di-setup untuk menggunakan local gateway:

```env
# Grok API Configuration (Local Gateway)
GROK_API_URL=http://localhost:8017/v1/chat/completions
GROK_API_KEY=grok-blog-generator
USE_LOCAL_GATEWAY=true

# Site Configuration
SITE_URL=https://yoursite.com
SITE_NAME=Viral News Hub
SITE_DESCRIPTION=Berita Terkini & Viral dari Seluruh Dunia
```

**CATATAN**: 
- `GROK_API_KEY` adalah dummy key (tidak digunakan untuk local gateway)
- `USE_LOCAL_GATEWAY=true` memberitahu sistem untuk menggunakan gateway lokal

---

## 🔄 Workflow

```
1. Start Grok API Gateway
   ↓
2. Add Grok Token (via admin panel)
   ↓
3. Verify token active
   ↓
4. Run blog generator
   ↓
5. Content generated!
```

---

## 💡 Tips

### Untuk Development

```bash
# Terminal 1: Run Grok API Gateway
python main.py

# Terminal 2: Generate content
python blog_generator.py --test
python build_site.py
cd public && python -m http.server 8000
```

### Untuk Production (GitHub Actions)

Anda perlu hosting Grok API Gateway di server yang bisa diakses oleh GitHub Actions, atau:

**Alternative**: Gunakan Grok API official (jika tersedia) dengan API key asli.

---

## 📞 Need Help?

Jika masih ada masalah:

1. **Check Grok API Gateway logs** di terminal yang running `python main.py`
2. **Check admin panel** untuk status token
3. **Review error messages** dengan teliti
4. **Test endpoints** dengan curl/Postman

---

## 🎯 Next Steps

Setelah berhasil generate 1 artikel test:

1. ✅ Generate lebih banyak artikel:
   ```bash
   python blog_generator.py --count 10
   ```

2. ✅ Build static site:
   ```bash
   python build_site.py
   ```

3. ✅ Preview:
   ```bash
   cd public
   python -m http.server 8000
   ```

4. ✅ Deploy ke GitHub Pages (lihat README-ID.md)

---

<div align="center">

**Setup Complete! 🎉**

*Sekarang Anda siap untuk auto-generate konten blog berkualitas tinggi!*

</div>

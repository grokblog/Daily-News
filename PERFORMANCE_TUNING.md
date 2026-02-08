# 🚀 Performance Tuning Guide - Grok Blog Generator

Panduan ini membantu Anda mengoptimalkan kinerja blog generator untuk kecepatan dan stabilitas maksimal, menggunakan fitur Parallel Generation yang baru.

## ⚙️ Konfigurasi Threading

Blog generator sekarang menggunakan **Multi-threading** untuk memproses beberapa artikel secara bersamaan.

### Cara Mengubah Jumlah Thread

Edit file `blog_generator.py`:

```python
def generate_batch(self, count: int = None):
    # ...
    max_workers = 3  # <-- UBAH ANGKA INI
```

### Rekomendasi Setting `max_workers`:

| Jumlah Token Grok | Recommended Threads | Est. Speed (Articles/Min) | Risk Level |
|-------------------|---------------------|---------------------------|------------|
| 1 Token           | 1 (Sequential)      | 0.5 - 1                   | Low        |
| 2-3 Tokens        | 2 Threads           | 1 - 2                     | Low        |
| 5+ Tokens         | 3-5 Threads         | 3 - 5                     | Medium     |
| 10+ Tokens        | 5-8 Threads         | 5 - 8                     | Medium     |

**⚠️ PENTING**: Jangan set `max_workers` terlalu tinggi jika token sedikit. Akibatnya bisa rate limit (429) atau banned.

---

## 🔄 Token Rotation Strategy

Sistem Grok API Gateway Anda memiliki fitur **Smart Token Rotation**.

1. **Load Balancing**: Request akan didistribusikan ke token yang memiliki sisa kuota terbanyak.
2. **Failover**: Jika satu token gagal (expired/limit), gateway otomatis mencoba token lain.

**Tips Optimalisasi Token:**
- Tambahkan minimal **3-5 akun Grok** berbeda ke `data/tokens.json` (via Admin Panel).
- Campur akun **Grok Premium** (jika ada) dan **Free** untuk cadangan.

---

## 🛠️ Troubleshooting Connection

Jika Anda melihat error:
`ProxyError` atau `ConnectionRefused` ke `localhost:8017`:

1. **Check Gateway**: Pastikan `python main.py` running.
2. **Disable System Proxy**: Script `grok_client.py` sudah di-update untuk bypass system proxy, tapi pastikan tidak ada VPN/Firewall yang memblokir localhost.

---

## 📈 Monitoring

Saat menjalankan `python blog_generator.py`, perhatikan log:

```
INFO:__main__:Starting batch generation: 10 articles (Parallel: 3 threads)
...
INFO:__main__:Batch generation complete: 10/10 articles generated
```

Jika banyak error 429/500, kurangi `max_workers` atau tambah token.

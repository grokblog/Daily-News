# 🚫 How to Fix "IP Blocked" (403 Error)

Grok API Gateway Anda diblokir oleh Cloudflare karena IP Anda terdeteksi melakukan traffic bot yang mencurigakan, atau token `cf_clearance` sudah expired.

## Solusi 1: Update `cf_clearance` (Paling Sering Berhasil)

Token Cloudflare (`cf_clearance`) terikat dengan sesi browser dan IP Anda. Jika expired, Anda harus update.

1.  Buka **grok.com** di browser (gunakan Incognito lebih baik).
2.  Login seperti biasa.
3.  Tekan **F12** untuk membuka Developer Tools.
4.  Buka tab **Application** (Chrome/Edge) atau **Storage** (Firefox).
5.  Di menu kiri, pilih **Cookies** -> `https://grok.com`.
6.  Cari cookie bernama `cf_clearance`.
7.  Copy Value-nya (string panjang).
8.  Buka file `data/setting.toml` di editor teks.
9.  Update baris:
    ```toml
    cf_clearance = "PASTE_VALUE_BARU_DISINI"
    ```
10. **Restart `main.py`** (Ctrl+C lalu run lagi).

## Solusi 2: Gunakan Proxy (Jika IP Benar-benar Diblokir)

Jika cara di atas gagal, IP Anda mungkin masuk blacklist sementara. Gunakan proxy.

1.  Siapkan proxy (HTTP atau SOCKS5).
2.  Edit file `data/setting.toml`.
3.  Isi bagian `proxy_url`:
    ```toml
    proxy_url = "http://username:password@host:port"
    # atau
    proxy_url = "socks5://127.0.0.1:1080" (jika pakai VPN/Proxy app)
    ```
4.  **Restart `main.py`**.

## Solusi 3: Restart Router (Dynamic IP)

Jika Anda menggunakan internet rumahan dengan IP dinamis:
1.  Matikan router/modem selama 1 menit.
2.  Nyalakan kembali untuk dapat IP baru.
3.  Ulangi langkah "Update cf_clearance".

---

**Setelah melakukan salah satu solusi di atas:**
Test lagi dengan:
```bash
python blog_generator.py --test
```

# Grok for Learning Only

<div align="center">

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal.svg)](https://fastapi.tiangolo.com)

**OpenAI-Compatible API Gateway for Grok AI**

[English](readme-en.md) | [Bahasa Indonesia](readme-id.md)

</div>

---

## 🌟 Overview

**Grok for Learning Only** is a FastAPI-based reverse proxy that provides an OpenAI-compatible API interface for Grok AI. It supports streaming conversations, image generation, image editing, web search, deep thinking, and video generation with automatic load balancing across multiple tokens.

> ⚠️ **Disclaimer**: This project is for educational and research purposes only. Please comply with all applicable terms of service.

---

## ✨ Features

- **🔄 OpenAI-Compatible API** - Drop-in replacement for OpenAI's `/v1/chat/completions` endpoint
- **💬 Streaming Support** - Real-time streaming responses for chat completions
- **🎨 Image Generation** - Generate images using Grok's FLUX model
- **🎬 Video Generation** - Create videos from images with the `grok-imagine-0.9` model
- **📺 Video Upscaling** - Upscale generated videos to HD quality
- **🌐 Web Search** - Real-time web search integration
- **🧠 Deep Thinking** - Advanced reasoning with thinking models
- **⚖️ Load Balancing** - Automatic token rotation and load distribution
- **🔐 Admin Dashboard** - Modern dark-themed admin panel for management
- **💾 Cache Management** - Local caching for images and videos
- **📊 Usage Statistics** - Real-time token usage and status monitoring

---

## 📦 Installation

### Requirements

- Python 3.10+
- pip or pipenv

### Quick Start

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

The server will start on `http://0.0.0.0:8017` by default.

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `STORAGE_MODE` | Storage mode: `file`, `mysql`, or `redis` | `file` |
| `DATABASE_URL` | Database connection URL (for mysql/redis) | - |
| `WORKERS` | Number of worker processes | `1` |

### Admin Panel Settings

Access the admin panel at `/login` to configure:

| Setting | Description | Default |
|---------|-------------|---------|
| `admin_username` | Admin login username | `admin` |
| `admin_password` | Admin login password | `admin` |
| `image_mode` | Image return mode: `url` or `base64` | `url` |
| `base_url` | Service base URL for media access | - |
| `proxy_url` | HTTP proxy for Grok API | - |
| `api_key` | API authentication key | - |
| `x_statsig_id` | Anti-bot verification parameter | Auto-generated |
| `cf_clearance` | Cloudflare clearance token | - |

---

## 🔌 API Endpoints

### Chat Completions

```bash
POST /v1/chat/completions
```

**Example:**
```bash
curl http://localhost:8017/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "grok-4.1",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "stream": true
  }'
```

### Image Generation

Include drawing instructions in your message to trigger image generation:

```bash
curl http://localhost:8017/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "grok-4.1",
    "messages": [
      {"role": "user", "content": "Draw a beautiful sunset over mountains"}
    ]
  }'
```

### Video Generation

Use the `grok-imagine-0.9` model with an image input:

```bash
curl http://localhost:8017/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "grok-imagine-0.9",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "Make the sun rise"},
          {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
        ]
      }
    ]
  }'
```

### Video Upscaling

```bash
POST /v1/videos/upscale
```

**Example:**
```bash
curl http://localhost:8017/v1/videos/upscale \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"video_id": "your-video-id"}'
```

---

## 🤖 Available Models

| Model | Credits | Account Type | Image | Thinking | Web Search | Video |
|-------|---------|--------------|-------|----------|------------|-------|
| `grok-4.1` | 1 | Basic/Super | ✅ | ✅ | ✅ | ❌ |
| `grok-4.1-thinking` | 1 | Basic/Super | ✅ | ✅ | ✅ | ❌ |
| `grok-imagine-0.9` | - | Basic/Super | ✅ | ❌ | ❌ | ✅ |
| `grok-4-fast` | 1 | Basic/Super | ✅ | ✅ | ✅ | ❌ |
| `grok-4-fast-expert` | 4 | Basic/Super | ✅ | ✅ | ✅ | ❌ |
| `grok-4-expert` | 4 | Basic/Super | ✅ | ✅ | ✅ | ❌ |
| `grok-4-heavy` | 1 | Super Only | ✅ | ✅ | ✅ | ❌ |
| `grok-3-fast` | 1 | Basic/Super | ✅ | ❌ | ✅ | ❌ |

---

## 📊 Usage Limits

- **Basic Account**: 80 requests / 20 hours (free)
- **Super Account**: Higher limits (varies)

The system automatically balances load across all configured tokens.

---

## 🔧 Admin Endpoints

<details>
<summary>Click to expand admin API endpoints</summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/login` | Admin login page |
| GET | `/manage` | Admin dashboard |
| POST | `/api/login` | Admin authentication |
| POST | `/api/logout` | Admin logout |
| GET | `/api/tokens` | Get token list |
| POST | `/api/tokens/add` | Add tokens |
| POST | `/api/tokens/delete` | Delete tokens |
| POST | `/api/tokens/test` | Test token validity |
| GET | `/api/settings` | Get settings |
| POST | `/api/settings` | Update settings |
| GET | `/api/stats` | Get usage statistics |
| GET | `/api/cache/size` | Get cache size |
| POST | `/api/cache/clear` | Clear all cache |

</details>

---

## ⚠️ Important Notes

1. **Service URL Required**: Set the `base_url` in settings for image/video URLs to work correctly.
2. **403 Errors**: Usually caused by Cloudflare. Try:
   - Changing server IP
   - Configuring a proxy
   - Setting `cf_clearance` token
3. **Token Management**: Tokens are automatically rotated based on usage and rate limits.

---

## 📄 License

This project is for educational purposes only. Use responsibly and in accordance with applicable terms of service.

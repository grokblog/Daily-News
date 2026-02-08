"""
Blog Configuration
Konfigurasi untuk Auto-Generate Blog Content System
"""

import os
from typing import List, Dict

# Simple .env loader
def load_dotenv():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key:
                        os.environ[key] = value

load_dotenv()

class BlogConfig:
    """Konfigurasi utama blog"""
    
    # Site Information
    SITE_NAME = os.getenv("SITE_NAME", "Viral News Hub")
    SITE_DESCRIPTION = os.getenv("SITE_DESCRIPTION", "Latest & Viral News from Around the World")
    SITE_URL = os.getenv("SITE_URL", "https://yoursite.com")
    SITE_AUTHOR = os.getenv("SITE_AUTHOR", "Viral News Team")
    SITE_LANGUAGE = os.getenv("SITE_LANGUAGE", "en")
    
    # Theme Settings
    THEME = os.getenv("THEME", "mediumish")  # Mediumish-inspired theme
    DEFAULT_THEME_MODE = os.getenv("DEFAULT_THEME_MODE", "light")  # light or dark
    ENABLE_THEME_TOGGLE = True
    
    # Content Settings
    POSTS_PER_PAGE = 12
    EXCERPT_LENGTH = 160
    MIN_CONTENT_LENGTH = 1500  # Minimum words for quality content
    MAX_CONTENT_LENGTH = 3000  # Maximum words
    
    # SEO Settings
    ENABLE_SCHEMA_MARKUP = True
    ENABLE_OPEN_GRAPH = True
    ENABLE_TWITTER_CARDS = True
    ENABLE_SITEMAP = True
    ENABLE_RSS_FEED = True
    
    # Google News RSS Feeds (US Edition - Query Based for Stability)
    GOOGLE_NEWS_FEEDS = {
        "technology": "https://news.google.com/rss/search?q=technology&hl=en-US&gl=US&ceid=US:en",
        "business": "https://news.google.com/rss/search?q=business&hl=en-US&gl=US&ceid=US:en",
        "entertainment": "https://news.google.com/rss/search?q=entertainment&hl=en-US&gl=US&ceid=US:en",
        "sports": "https://news.google.com/rss/search?q=sports&hl=en-US&gl=US&ceid=US:en",
        "health": "https://news.google.com/rss/search?q=health&hl=en-US&gl=US&ceid=US:en",
        "science": "https://news.google.com/rss/search?q=science&hl=en-US&gl=US&ceid=US:en",
        "ai": "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
        "crypto": "https://news.google.com/rss/search?q=cryptocurrency&hl=en-US&gl=US&ceid=US:en"
    }
    
    # Grok API Settings
    GROK_API_URL = os.getenv("GROK_API_URL", "http://localhost:8017/v1/chat/completions")
    GROK_API_KEY = os.getenv("GROK_API_KEY", "grok-blog-generator")  # Dummy key, not used with local gateway
    GROK_MODEL = "grok-2"
    GROK_IMAGE_MODEL = "grok-2-image-gen"  # For image generation
    
    # Use local Grok API Gateway (no real API key needed)
    USE_LOCAL_GATEWAY = os.getenv("USE_LOCAL_GATEWAY", "true").lower() == "true"
    
    # Content Generation Settings
    ARTICLES_PER_RUN = 5  # Amount of articles to generate per run
    ENABLE_IMAGE_GENERATION = True
    IMAGES_PER_ARTICLE = 1  # Featured image
    
    # Quality Control
    MIN_UNIQUENESS_SCORE = 80  # Minimum uniqueness percentage
    ENABLE_GRAMMAR_CHECK = True
    ENABLE_SEO_ANALYSIS = True
    
    # Cron Schedule (for GitHub Actions)
    CRON_SCHEDULE = "0 */6 * * *"  # Every 6 hours
    
    # Output Directories
    OUTPUT_DIR = "public"
    POSTS_DIR = f"{OUTPUT_DIR}/posts"
    IMAGES_DIR = f"{OUTPUT_DIR}/images"
    ASSETS_DIR = f"{OUTPUT_DIR}/assets"
    
    # Cache Settings
    ENABLE_CACHE = True
    CACHE_DIR = ".cache"
    CACHE_EXPIRY_HOURS = 24
    
    # Schema.org Types
    SCHEMA_TYPES = [
        "NewsArticle",
        "Article",
        "BlogPosting",
    ]
    
    # Social Media
    TWITTER_HANDLE = "@yournewssite"
    FACEBOOK_APP_ID = ""
    
    @classmethod
    def get_feed_urls(cls) -> List[str]:
        """Get all RSS feed URLs"""
        return list(cls.GOOGLE_NEWS_FEEDS.values())
    
    @classmethod
    def get_categories(cls) -> List[str]:
        """Get all category names"""
        return list(cls.GOOGLE_NEWS_FEEDS.keys())
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration"""
        if cls.USE_LOCAL_GATEWAY:
            # When using local gateway, just check if URL is set
            if not cls.GROK_API_URL:
                raise ValueError("GROK_API_URL is required (should be http://localhost:8017/v1/chat/completions)")
        else:
            # When using external API, require API key
            if not cls.GROK_API_KEY or cls.GROK_API_KEY == "grok-blog-generator":
                raise ValueError("GROK_API_KEY is required when not using local gateway")
        
        if not cls.SITE_URL:
            raise ValueError("SITE_URL is required")
        return True


# Prompt Templates for Grok
CONTENT_REWRITE_PROMPT = """
Task: You are a senior journalist and SEO expert. Your task is to rewrite the following news article into a comprehensive, unique, and engaging blog post in English.

Input Article Data:
{original_content}

Writing Instructions:
1.  **Analysis**: Extract key facts, quotes, and data from the input text. Ignore promotional text, navigation menus, or ads.
    *CRITICAL*: If the input text is short or just a snippet (due to paywall), USE YOUR OWN KNOWLEDGE to expand on the topic comprehensively based on the Title/Keywords. Do not complain about missing text.
2.  **Unique Angle**: Rewrite with a fresh and engaging perspective. Do not just translate or summarize. Target US audience.
3.  **SEO Structure**:
    -   **Title**: Create a click-worthy but accurate title (50-60 chars), containing keyword "{keyword}".
    Key Requirements:
    1. Tone: Professional, authoritative, yet accessible. Avoid robotic or repetitive phrasing.
    2. Structure: Use H2 for main sections and H3 for subsections. Short paragraphs.
    3. Formatting: Use bullet points, bold text for emphasis.
    4. NO H1 tags in the content (Title is already H1).
    5. **Internal Links**: Include at least 2 internal links to other parts of the blog.
       - Use these formats: `<a href="/category/technology.html">Technology Section</a>`, `<a href="/">Viral News Hub</a>`, etc.
    6. **External Links**: Include at least 2 external links to authoritative sources (e.g., official announcements, major news outlets) with `target="_blank"`.
    7. SEO: Naturally weave the keywords into the first paragraph and headers.
    -   **Introduction**: Strong opening paragraph (hook) that immediately grabs attention.
    -   **Body**: Use 3-5 descriptive, punchy H2 subheadings. Break up long paragraphs.
    -   **Sub-sections**: Use H3 if needed for deep detail.
    -   **Conclusion**: Brief summary and a question to spark comment/discussion.
4.  **Style**:
    -   Use standard US English (modern journalistic style).
    -   Avoid passive voice.
    -   Tone: Informative, Authoritative, and Enthusiastic.
5.  **Length**: Minimum {min_words} words, Maximum {max_words} words.

Output Format (MUST BE JSON):
{{
  "title": "SEO Friendly Article Title",
  "meta_description": "Engaging summary 150-160 chars for Google Search snippet",
  "slug": "seo-friendly-url-slug",
  "excerpt": "Excerpt of the first paragraph (max 160 chars)",
  "content": "<p>Opening paragraph...</p><h2>Subheading 1</h2><p>Content...</p>...",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "category": "{category}",
  "tags": ["tag1", "tag2", "tag3"]
}}

IMPORTANT: OUTPUT ONLY THE JSON OBJECT. NO EXPLANATIONS. NO "HERE IS THE JSON". START THE RESPONSE WITH {{ AND END WITH }}.
"""

IMAGE_GENERATION_PROMPT = """
Subject: {topic}
Style: High-End Conceptual Editorial Photography, 16:9 aspect ratio, 8k resolution, photorealistic news thumbnail.
Mood: {mood}
Included Elements: {elements}
Composition: Cinematic lighting, depth of field, balanced composition, centered subject, wide shot.
Negative Prompt: Text, watermark, blur, low quality, distorted, cartoonish, 3d render, portrait, vertical.
"""

SEO_SCHEMA_TEMPLATE = """
Generate complete Schema.org markup (JSON-LD) for this article:

Title: {title}
Description: {description}
Category: {category}
Published Date: {date}
Author: {author}
Image URL: {image_url}
Article URL: {article_url}

Include these schema types:
- NewsArticle
- BreadcrumbList
- Organization (publisher)
- Person (author)

Return valid JSON-LD only.
"""

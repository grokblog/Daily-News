# Blog Generation Testing Guide

This guide explains how to test the automated blog content generation system, from generating articles to viewing them on your local server.

## Prerequisites

Before running the generator, ensure the **Grok API Gateway** is running.
1. Open a new terminal.
2. Navigate to your Grok Gateway folder (if separate) or ensure the local service is active on port `8017`.
   - **URL**: `http://localhost:8017`
   - **Endpoint**: `/v1/chat/completions`

## Step 1: Generate Content

To generate a single test article, use the `--test` flag. This will fetch news, rewrite it using Grok, generate an image, and save it as JSON.

```bash
python blog_generator.py --test
```

*Or to generate a specific number of articles:*
```bash
python blog_generator.py --count 3
```

**What happens:**
- Fetches RSS feeds (Google News).
- Selects the most viral/relevant topic.
- Rewrites content to be unique and SEO-friendly.
- Generates a **16:9** high-resolution thumbnail.
- Saves the article in `public/posts/[slug].json`.

## Step 2: Build the Website

After generating content (JSON files), you must build the static HTML site.

```bash
python build_site.py
```

**What happens:**
- Reads all JSON files from `public/posts/`.
- Renders HTML pages using templates.
- Updates the Homepage, Category pages, and Sitemap.
- Copies assets to `public/`.

## Step 3: View Results

Start a local web server to view the site.

```bash
python -m http.server 8000 --directory public
```

**Verification Checklist:**
1. Open `http://localhost:8000`.
2. Check the **Latest News** section for the new article.
3. **Images**: Verify the thumbnail is high-quality and 16:9 aspect ratio.
4. **Content**: Open the article and check:
   - **Internal Links**: Are there links to categories (e.g., "Technology")?
   - **External Links**: Are there links to sources (e.g., Apple, Google)?
   - **Structure**: Are there proper H2/H3 headings?
5. **Google Discover**: View page source (`Ctrl+U`) and search for `<meta name="robots" content="max-image-preview:large">`.

## Troubleshooting

- **Connection Error**: If `blog_generator.py` fails with connection errors, check if Grok Gateway is running on port 8017.
- **Missing Images**: Ensure `Pillow` is installed and the `public/images` folder exists.
- **Language**: The site is configured for strict English. If you see Indonesian, try rebuilding the site.

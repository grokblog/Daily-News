"""
Blog Generator
Main script untuk generate blog content
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import time

from blog_config import BlogConfig
from grok_client import GrokClient
from rss_parser import RSSParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BlogGenerator:
    """Main blog content generator"""
    
    def __init__(self):
        self.config = BlogConfig()
        self.grok = GrokClient()
        self.rss_parser = RSSParser()
        self.cache_file = Path(BlogConfig.CACHE_DIR) / "processed_articles.json"
        self.processed_ids = self._load_processed_ids()
        
        # Create directories
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        dirs = [
            BlogConfig.OUTPUT_DIR,
            BlogConfig.POSTS_DIR,
            BlogConfig.IMAGES_DIR,
            BlogConfig.ASSETS_DIR,
            BlogConfig.CACHE_DIR
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        logger.info("Directories created")
    
    def _load_processed_ids(self) -> set:
        """Load processed article IDs from cache"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('processed_ids', []))
            except:
                return set()
        return set()
    
    def _save_processed_id(self, article_id: str):
        """Save processed article ID to cache"""
        self.processed_ids.add(article_id)
        
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'processed_ids': list(self.processed_ids),
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)
    
    def fetch_articles(self) -> List[Dict]:
        """Fetch articles from RSS feeds"""
        logger.info("Fetching articles from RSS feeds...")
        
        articles = self.rss_parser.parse_all_feeds(BlogConfig.GOOGLE_NEWS_FEEDS)
        
        # Filter out already processed articles
        new_articles = [
            article for article in articles 
            if article['id'] not in self.processed_ids
        ]
        
        logger.info(f"Found {len(new_articles)} new articles")
        
        # Calculate viral scores
        for article in new_articles:
            article['viral_score'] = self.rss_parser.get_viral_potential_score(article)
        
        # Sort by viral potential
        new_articles.sort(key=lambda x: x['viral_score'], reverse=True)
        
        return new_articles
    
    def generate_article(self, source_article: Dict) -> Optional[Dict]:
        """
        Generate blog article from source
        
        Args:
            source_article: Source article dict from RSS
        
        Returns:
            Generated article dict or None if failed
        """
        logger.info(f"Generating article: {source_article['title']}")
        
        try:
            # Extract main keyword
            keyword = source_article['keywords'][0] if source_article['keywords'] else source_article['title']
            
            # Fetch full content if available
            full_content = self.rss_parser.fetch_article_content(source_article['url'])
            
            # Construct richer input text to avoid "snippet" confusion
            content_body = full_content if full_content else source_article['description']
            input_text = f"Title: {source_article['title']}\nSource: {source_article['source']}\n\nContent:\n{content_body}"
            
            # Rewrite content with Grok
            rewritten = self.grok.rewrite_content(
                original_content=input_text,
                keyword=keyword,
                category=source_article['category'],
                min_words=BlogConfig.MIN_CONTENT_LENGTH,
                max_words=BlogConfig.MAX_CONTENT_LENGTH
            )
            
            if not rewritten:
                logger.error(f"Failed to rewrite article: {source_article['title']}")
                return None
            
            # Generate featured image
            image_url = ""
            if BlogConfig.ENABLE_IMAGE_GENERATION:
                try:
                    image_url = self.grok.generate_image(
                        topic=rewritten['title'],
                        mood="professional and engaging",
                        elements=f"related to {source_article['category']}"
                    )
                    
                    # Download and save image
                    if image_url:
                        image_filename = self._download_image(image_url, rewritten['slug'])
                        if image_filename:
                            image_url = f"/images/{image_filename}"
                except Exception as e:
                    logger.error(f"Image generation failed: {e}")
            
            # Generate publication date
            pub_date = datetime.now()
            
            # Generate schema markup
            article_url = f"{BlogConfig.SITE_URL}/posts/{rewritten['slug']}.html"
            schema_image_url = f"{BlogConfig.SITE_URL}{image_url}" if image_url.startswith('/') else image_url
            
            schema = self.grok.generate_schema(
                title=rewritten['title'],
                description=rewritten['meta_description'],
                category=rewritten['category'],
                date=pub_date.isoformat(),
                author=BlogConfig.SITE_AUTHOR,
                image_url=schema_image_url,
                article_url=article_url
            )
            
            # Compile final article
            article = {
                'id': source_article['id'],
                'title': rewritten['title'],
                'slug': rewritten['slug'],
                'excerpt': rewritten['excerpt'],
                'content': rewritten['content'],
                'meta_description': rewritten['meta_description'],
                'keywords': rewritten['keywords'],
                'tags': rewritten.get('tags', []),
                'category': rewritten['category'],
                'featured_image': image_url,
                'author': BlogConfig.SITE_AUTHOR,
                'published_date': pub_date.isoformat(),
                'modified_date': pub_date.isoformat(),
                'schema': schema,
                'source_url': source_article['url'],
                'source_title': source_article['title'],
                'viral_score': source_article['viral_score']
            }
            
            logger.info(f"Successfully generated article: {article['title']}")
            return article
        
        except Exception as e:
            logger.error(f"Failed to generate article: {e}")
            return None
    
    def _download_image(self, image_url: str, slug: str) -> Optional[str]:
        """Download and save image"""
        try:
            import requests
            from PIL import Image
            from io import BytesIO
            
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Open image
            img = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Force 16:9 Aspect Ratio (1200x675) for Google Discover
            from PIL import ImageOps
            target_width = 1200
            target_height = 675
            img = ImageOps.fit(img, (target_width, target_height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            
            # Save image
            filename = f"{slug}-{int(time.time())}.jpg"
            filepath = Path(BlogConfig.IMAGES_DIR) / filename
            
            img.save(filepath, 'JPEG', quality=85, optimize=True)
            
            logger.info(f"Image saved: {filename}")
            return filename
        
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            return None
    
    def save_article(self, article: Dict):
        """Save article to JSON file"""
        filename = f"{article['slug']}.json"
        filepath = Path(BlogConfig.POSTS_DIR) / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(article, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Article saved: {filename}")
        
        # Mark as processed
        self._save_processed_id(article['id'])
    
    def generate_batch(self, count: int = None):
        """
        Generate batch of articles (Parallel Version)
        
        Args:
            count: Number of articles to generate (default: from config)
        """
        import concurrent.futures
        import threading
        
        count = count or BlogConfig.ARTICLES_PER_RUN
        max_workers = 3  # Parallel workers
        
        logger.info(f"Starting batch generation: {count} articles (Parallel: {max_workers} threads)")
        
        # Fetch articles
        articles = self.fetch_articles()
        
        if not articles:
            logger.warning("No new articles found")
            return
        
        # Limit to requested count
        articles_to_process = articles[:count]
        generated_count = 0
        
        # Thread lock for file operations
        file_lock = threading.Lock()
        
        def process_single_article(source_article):
            try:
                # Generate article
                article = self.generate_article(source_article)
                
                if article:
                    # Save with lock to prevent race conditions
                    with file_lock:
                        self.save_article(article)
                        # save_article already calls _save_processed_id
                    return True
            except Exception as e:
                logger.error(f"Error processing article {source_article['title']}: {e}")
            return False

        # Execute in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(process_single_article, articles_to_process))
            
        generated_count = sum(1 for r in results if r)
        logger.info(f"Batch generation complete: {generated_count}/{len(articles_to_process)} articles generated")
    
    def get_all_articles(self) -> List[Dict]:
        """Get all generated articles"""
        articles = []
        
        posts_dir = Path(BlogConfig.POSTS_DIR)
        for json_file in posts_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    article = json.load(f)
                    articles.append(article)
            except Exception as e:
                logger.error(f"Error reading {json_file}: {e}")
        
        # Sort by date (newest first)
        articles.sort(key=lambda x: x['published_date'], reverse=True)
        
        return articles


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Blog Content Generator')
    parser.add_argument('--count', type=int, help='Number of articles to generate')
    parser.add_argument('--test', action='store_true', help='Test mode (generate 1 article)')
    
    args = parser.parse_args()
    
    # Validate config
    BlogConfig.validate_config()
    
    # Create generator
    generator = BlogGenerator()
    
    # Generate articles
    if args.test:
        logger.info("Running in test mode")
        generator.generate_batch(count=1)
    else:
        generator.generate_batch(count=args.count)


if __name__ == "__main__":
    main()

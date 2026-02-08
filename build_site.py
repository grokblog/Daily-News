"""
Build Site
Generate static HTML site from blog data
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from jinja2 import Environment, FileSystemLoader
import logging

from blog_config import BlogConfig
from blog_generator import BlogGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SiteBuilder:
    """Build static HTML site"""
    
    def __init__(self):
        self.config = BlogConfig()
        self.generator = BlogGenerator()
        
        # Setup Jinja2
        self.jinja_env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=True
        )
        
        # Add custom filters
        self.jinja_env.filters['format_date'] = self.format_date
        self.jinja_env.filters['reading_time'] = self.calculate_reading_time
        
        self.articles = []
    
    def format_date(self, date_str: str) -> str:
        """Format ISO date to readable format (English)"""
        try:
            dt = datetime.fromisoformat(date_str)
            months = [
                "January", "February", "March", "April", "May", "June", 
                "July", "August", "September", "October", "November", "December"
            ]
            return f"{dt.day} {months[dt.month - 1]} {dt.year}"
        except:
            return date_str
    
    def calculate_reading_time(self, content: str) -> int:
        """Calculate reading time in minutes"""
        words = len(content.split())
        return max(1, round(words / 200))  # 200 words per minute
    
    def load_articles(self):
        """Load all articles"""
        logger.info("Loading articles...")
        self.articles = self.generator.get_all_articles()
        logger.info(f"Loaded {len(self.articles)} articles")
    
    def build_article_page(self, article: Dict):
        """Build individual article page"""
        template = self.jinja_env.get_template('article.html')
        
        # Get related articles (same category, limit 3)
        related = [
            a for a in self.articles 
            if a['category'] == article['category'] and a['id'] != article['id']
        ][:3]
        
        # Render template
        html = template.render(
            article=article,
            title=article['title'],
            meta_description=article['meta_description'],
            keywords=', '.join(article['keywords']),
            author=article['author'],
            article_url=f"{BlogConfig.SITE_URL}/posts/{article['slug']}.html",
            featured_image=article['featured_image'],
            published_date=article['published_date'],
            published_date_formatted=self.format_date(article['published_date']),
            reading_time=self.calculate_reading_time(article['content']),
            category=article['category'],
            tags=article['tags'],
            content=article['content'],
            schema_json=json.dumps(article['schema'], ensure_ascii=False),
            site_name=BlogConfig.SITE_NAME,
            site_description=BlogConfig.SITE_DESCRIPTION,
            current_year=datetime.now().year,
            related_articles=related
        )
        
        # Save HTML file
        output_path = Path(BlogConfig.POSTS_DIR) / f"{article['slug']}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Built article page: {article['slug']}.html")
    
    def build_index_page(self):
        """Build homepage"""
        template = self.jinja_env.get_template('index.html')
        
        # Get featured articles (top 6 by viral score)
        featured = sorted(
            self.articles,
            key=lambda x: x.get('viral_score', 0),
            reverse=True
        )[:6]
        
        # Get recent articles
        recent = self.articles[:12]
        
        # Group by category
        by_category = {}
        for article in self.articles:
            cat = article['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(article)
        
        html = template.render(
            featured_articles=featured,
            recent_articles=recent,
            categories=by_category,
            site_name=BlogConfig.SITE_NAME,
            site_description=BlogConfig.SITE_DESCRIPTION,
            current_year=datetime.now().year
        )
        
        output_path = Path(BlogConfig.OUTPUT_DIR) / 'index.html'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info("Built index page")
    
    def build_category_pages(self):
        """Build category pages"""
        template = self.jinja_env.get_template('category.html')
        
        # Group articles by category
        by_category = {}
        for article in self.articles:
            cat = article['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(article)
        
        # Create category directory
        category_dir = Path(BlogConfig.OUTPUT_DIR) / 'category'
        category_dir.mkdir(exist_ok=True)
        
        # Build page for each category
        for category, articles in by_category.items():
            html = template.render(
                category=category,
                articles=articles,
                site_name=BlogConfig.SITE_NAME,
                current_year=datetime.now().year
            )
            
            output_path = category_dir / f"{category}.html"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            logger.info(f"Built category page: {category}")
    
    def build_sitemap(self):
        """Generate sitemap.xml"""
        sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
        sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        
        # Homepage
        sitemap.append('  <url>')
        sitemap.append(f'    <loc>{BlogConfig.SITE_URL}/</loc>')
        sitemap.append(f'    <lastmod>{datetime.now().date().isoformat()}</lastmod>')
        sitemap.append('    <changefreq>daily</changefreq>')
        sitemap.append('    <priority>1.0</priority>')
        sitemap.append('  </url>')
        
        # Articles
        for article in self.articles:
            sitemap.append('  <url>')
            sitemap.append(f'    <loc>{BlogConfig.SITE_URL}/posts/{article["slug"]}.html</loc>')
            sitemap.append(f'    <lastmod>{article["modified_date"][:10]}</lastmod>')
            sitemap.append('    <changefreq>weekly</changefreq>')
            sitemap.append('    <priority>0.8</priority>')
            sitemap.append('  </url>')
        
        # Categories
        for category in BlogConfig.get_categories():
            sitemap.append('  <url>')
            sitemap.append(f'    <loc>{BlogConfig.SITE_URL}/category/{category}.html</loc>')
            sitemap.append(f'    <lastmod>{datetime.now().date().isoformat()}</lastmod>')
            sitemap.append('    <changefreq>daily</changefreq>')
            sitemap.append('    <priority>0.7</priority>')
            sitemap.append('  </url>')
        
        sitemap.append('</urlset>')
        
        output_path = Path(BlogConfig.OUTPUT_DIR) / 'sitemap.xml'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sitemap))
        
        logger.info("Built sitemap.xml")
    
    def build_rss_feed(self):
        """Generate RSS feed"""
        rss = ['<?xml version="1.0" encoding="UTF-8"?>']
        rss.append('<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">')
        rss.append('  <channel>')
        rss.append(f'    <title>{BlogConfig.SITE_NAME}</title>')
        rss.append(f'    <link>{BlogConfig.SITE_URL}</link>')
        rss.append(f'    <description>{BlogConfig.SITE_DESCRIPTION}</description>')
        rss.append(f'    <language>{BlogConfig.SITE_LANGUAGE}</language>')
        rss.append(f'    <lastBuildDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")}</lastBuildDate>')
        rss.append(f'    <atom:link href="{BlogConfig.SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />')
        
        # Add articles (latest 20)
        for article in self.articles[:20]:
            rss.append('    <item>')
            rss.append(f'      <title>{self._escape_xml(article["title"])}</title>')
            rss.append(f'      <link>{BlogConfig.SITE_URL}/posts/{article["slug"]}.html</link>')
            rss.append(f'      <description>{self._escape_xml(article["excerpt"])}</description>')
            rss.append(f'      <pubDate>{datetime.fromisoformat(article["published_date"]).strftime("%a, %d %b %Y %H:%M:%S %z")}</pubDate>')
            rss.append(f'      <guid>{BlogConfig.SITE_URL}/posts/{article["slug"]}.html</guid>')
            rss.append(f'      <category>{article["category"]}</category>')
            if article.get('featured_image'):
                rss.append(f'      <enclosure url="{article["featured_image"]}" type="image/jpeg" />')
            rss.append('    </item>')
        
        rss.append('  </channel>')
        rss.append('</rss>')
        
        output_path = Path(BlogConfig.OUTPUT_DIR) / 'feed.xml'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(rss))
        
        logger.info("Built RSS feed")
    
    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))
    
    def copy_assets(self):
        """Copy static assets"""
        logger.info("Copying assets...")
        
        # Copy CSS
        src_css = Path('templates/assets/css')
        dst_css = Path(BlogConfig.OUTPUT_DIR) / 'assets' / 'css'
        dst_css.mkdir(parents=True, exist_ok=True)
        
        if src_css.exists():
            for css_file in src_css.glob('*.css'):
                shutil.copy2(css_file, dst_css / css_file.name)
        
        # Copy JS
        src_js = Path('templates/assets/js')
        dst_js = Path(BlogConfig.OUTPUT_DIR) / 'assets' / 'js'
        dst_js.mkdir(parents=True, exist_ok=True)
        
        if src_js.exists():
            for js_file in src_js.glob('*.js'):
                shutil.copy2(js_file, dst_js / js_file.name)
        
        # Copy images
        src_images = Path(BlogConfig.IMAGES_DIR)
        dst_images = Path(BlogConfig.OUTPUT_DIR) / 'images'
        dst_images.mkdir(parents=True, exist_ok=True)
        
        if src_images.exists():
            for img_file in src_images.glob('*'):
                if img_file.is_file():
                    try:
                        # Check if src and dst are different paths, otherwise skip
                        dst_path = dst_images / img_file.name
                        if img_file.resolve() != dst_path.resolve():
                            shutil.copy2(img_file, dst_path)
                    except shutil.SameFileError:
                        pass  # Ignore if same file
                    except Exception as e:
                        logger.warning(f"Failed to copy asset {img_file}: {e}")
        
        logger.info("Assets copied")
    
    def build_all(self):
        """Build entire site"""
        logger.info("Starting site build...")
        self.load_articles()
        
        if not self.articles:
            logger.warning("No articles found. Generating placeholder site structure...")
            # Create a placeholder 'Welcome' article so list is not empty
            self.articles = [{
                'id': 'welcome',
                'title': 'Welcome to Viral News Hub',
                'slug': 'welcome',
                'excerpt': 'Welcome to your new AI-powered blog. Start generating content to see it appear here.',
                'content': '<p>This is a placeholder article. Please run the generator to populate your blog with amazing content!</p>',
                'meta_description': 'Welcome to Viral News Hub',
                'keywords': ['welcome'],
                'tags': ['welcome'],
                'category': 'General',
                'featured_image': 'https://via.placeholder.com/800x400?text=Welcome+to+Viral+News+Hub',
                'author': BlogConfig.SITE_AUTHOR,
                'published_date': datetime.now().isoformat(),
                'modified_date': datetime.now().isoformat(),
                'viral_score': 100
            }]
        
        logger.info("Building article pages...")
        for article in self.articles:
            self.build_article_page(article)
            
        self.build_index_page()
        self.build_category_pages()
        self.build_sitemap()
        self.build_rss_feed()
        self.copy_assets()
        
        logger.info(f"✅ Site build complete! {len(self.articles)} articles published.")
        logger.info(f"Output directory: {Path(BlogConfig.OUTPUT_DIR).absolute()}")


def main():
    """Main entry point"""
    builder = SiteBuilder()
    builder.build_all()


if __name__ == "__main__":
    main()

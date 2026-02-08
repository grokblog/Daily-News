"""
RSS Feed Parser
Parse Google News RSS feeds and extract articles
"""

import feedparser
import requests
from typing import List, Dict, Optional
from datetime import datetime
import logging
from urllib.parse import urlparse, parse_qs
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RSSParser:
    """Parser untuk Google News RSS feeds"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def parse_feed(self, feed_url: str, category: str) -> List[Dict]:
        """
        Parse RSS feed and extract articles using requests session (bypass strict bot protection)
        
        Args:
            feed_url: RSS feed URL
            category: Category name
        
        Returns:
            List of article dicts
        """
        logger.info(f"Parsing feed: {category}")
        
        try:
            # Explicitly fetch with session to use browser headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://news.google.com/"
            }
            
            response = self.session.get(feed_url, headers=headers, timeout=20)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch feed {category}: Status {response.status_code}")
                return []
                
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                logger.warning(f"Feed fetched but empty entries for {category}")
                
            articles = []
            
            for entry in feed.entries:
                article = self._extract_article_data(entry, category)
                if article:
                    articles.append(article)
            
            logger.info(f"Found {len(articles)} articles in {category}")
            return articles
        
        except Exception as e:
            logger.error(f"Error parsing feed {category}: {e}")
            return []
    
    def _extract_article_data(self, entry, category: str) -> Optional[Dict]:
        """Extract article data from feed entry"""
        try:
            # Get article URL (Google News redirects)
            link = entry.get('link', '')
            
            # Extract actual article URL from Google News redirect
            actual_url = self._extract_actual_url(link)
            
            # Get published date
            published = entry.get('published_parsed')
            if published:
                pub_date = datetime(*published[:6])
            else:
                pub_date = datetime.now()
            
            # Get title and description
            title = entry.get('title', '')
            description = entry.get('summary', '')
            
            # Get source
            source = entry.get('source', {}).get('title', 'Unknown')
            
            # Generate unique ID
            article_id = self._generate_article_id(title, actual_url)
            
            # Extract keywords from title
            keywords = self._extract_keywords(title)
            
            return {
                'id': article_id,
                'title': title,
                'description': description,
                'url': actual_url,
                'source': source,
                'category': category,
                'published_date': pub_date.isoformat(),
                'keywords': keywords,
                'raw_content': description  # Will be enriched later
            }
        
        except Exception as e:
            logger.error(f"Error extracting article data: {e}")
            return None
    
    def _extract_actual_url(self, google_url: str) -> str:
        """
        Extract actual URL from Google News redirect
        """
        try:
            # 1. Try Base64 decoding (often hides in the URL)
            import base64
            import re
            
            # Pattern for new Google News URLs (often contain the url within base64 sections)
            # This is complex, so we will try the direct approach first:
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
            
            # 2. Fetch the redirect page
            response = self.session.get(google_url, headers=headers, allow_redirects=True, timeout=10)
            
            # Check if we are already at the destination
            if "news.google.com" not in response.url:
                return response.url
                
            # 3. If still on google, parse HTML for the link
            # Google often puts the real link in a redirect <a> tag or JS
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for "opening..." link
            links = soup.find_all('a')
            for link in links:
                href = link.get('href')
                if href and href.startswith('http') and 'google.com' not in href:
                    return href
                    
            # 4. Try regex for JS redirect
            match = re.search(r'window\.location\.replace\("([^"]+)"\)', response.text)
            if match:
                return match.group(1)
            
            return response.url
            
        except Exception as e:
            logger.warning(f"Failed to resolve URL {google_url}: {e}")
            return google_url

    def _generate_article_id(self, title: str, url: str) -> str:
        """Generate unique article ID"""
        content = f"{title}{url}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _extract_keywords(self, title: str) -> List[str]:
        """Extract potential keywords from title"""
        # Simple keyword extraction - can be improved with NLP
        stopwords = {
            'dan', 'atau', 'yang', 'di', 'ke', 'dari', 'untuk', 'pada',
            'dengan', 'adalah', 'ini', 'itu', 'akan', 'telah', 'sudah',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to'
        }
        
        words = title.lower().split()
        keywords = [
            word.strip('.,!?;:') 
            for word in words 
            if len(word) > 3 and word.lower() not in stopwords
        ]
        
        return keywords[:5]  # Return top 5 keywords
    
    def fetch_article_content(self, url: str) -> Optional[str]:
        """
        Fetch full article content from URL with improved heuristics
        
        Args:
            url: Article URL
        
        Returns:
            Article content text
        """
        try:
            # Resolve actual URL if it's a Google News link
            if "news.google.com" in url:
                url = self._extract_actual_url(url)
                logger.info(f"Resolved URL: {url}")

            # Add headers to mimic browser
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://news.google.com/"
            }
            
            response = self.session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            import re
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "header", "footer", "iframe", "noscript", "aside"]):
                element.decompose()
            
            # Remove promotional/ads divs (common classes)
            for div in soup.find_all("div", class_=re.compile(r'(ad|promo|social|sidebar|newsletter|comment|related)', re.I)):
                div.decompose()
            
            # Strategy 1: Look for <article> tag
            article = soup.find('article')
            if article:
                text = article.get_text(separator=' ', strip=True)
                if len(text) > 500:
                    return self._clean_text(text)
            
            # Strategy 2: Look for main content div by class name
            main_content = soup.find("div", class_=re.compile(r'(article-body|entry-content|post-content|story-body|main-content)', re.I))
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
                if len(text) > 500:
                    return self._clean_text(text)
            
            # Strategy 3: Find div with most <p> tags
            divs = soup.find_all('div')
            best_div = None
            max_p_len = 0
            
            for div in divs:
                # Count total length of text in <p> tags
                p_text_len = sum(len(p.get_text()) for p in div.find_all('p', recursive=False))
                if p_text_len > max_p_len:
                    max_p_len = p_text_len
                    best_div = div
            
            if best_div and max_p_len > 500:
                text = best_div.get_text(separator=' ', strip=True)
                return self._clean_text(text)
            
            # Fallback: Get all text if strategies fail
            text = soup.get_text(separator=' ', strip=True)
            return self._clean_text(text)
        
        except Exception as e:
            logger.error(f"Error fetching article content from {url}: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """Clean up text"""
        # Remove extra whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def parse_all_feeds(self, feeds: Dict[str, str]) -> List[Dict]:
        """
        Parse all RSS feeds
        
        Args:
            feeds: Dict of category -> feed_url
        
        Returns:
            List of all articles
        """
        all_articles = []
        
        for category, feed_url in feeds.items():
            articles = self.parse_feed(feed_url, category)
            all_articles.extend(articles)
        
        logger.info(f"Total articles parsed: {len(all_articles)}")
        return all_articles
    
    def get_viral_potential_score(self, article: Dict) -> float:
        """
        Calculate viral potential score for article
        
        Args:
            article: Article dict
        
        Returns:
            Score from 0-100
        """
        score = 50.0  # Base score
        
        title = article.get('title', '').lower()
        
        # Viral keywords boost
        viral_keywords = [
            'viral', 'trending', 'heboh', 'mengejutkan', 'terbaru',
            'breaking', 'eksklusif', 'rahasia', 'terungkap', 'sensational'
        ]
        
        for keyword in viral_keywords:
            if keyword in title:
                score += 10
        
        # Category boost
        viral_categories = ['hiburan', 'teknologi', 'olahraga']
        if article.get('category') in viral_categories:
            score += 5
        
        # Recency boost
        try:
            pub_date = datetime.fromisoformat(article.get('published_date', ''))
            hours_old = (datetime.now() - pub_date).total_seconds() / 3600
            
            if hours_old < 6:
                score += 15
            elif hours_old < 24:
                score += 10
            elif hours_old < 48:
                score += 5
        except:
            pass
        
        return min(score, 100.0)


# Test function
if __name__ == "__main__":
    from blog_config import BlogConfig
    
    parser = RSSParser()
    articles = parser.parse_all_feeds(BlogConfig.GOOGLE_NEWS_FEEDS)
    
    # Sort by viral potential
    for article in articles:
        article['viral_score'] = parser.get_viral_potential_score(article)
    
    articles.sort(key=lambda x: x['viral_score'], reverse=True)
    
    # Print top 5
    print("\nTop 5 Viral Potential Articles:")
    for i, article in enumerate(articles[:5], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Category: {article['category']}")
        print(f"   Viral Score: {article['viral_score']}")
        print(f"   Source: {article['source']}")

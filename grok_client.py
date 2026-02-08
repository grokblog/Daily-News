"""
Grok AI Client
Client untuk berinteraksi dengan Grok API
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any
from blog_config import BlogConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GrokClient:
    """Client untuk Grok AI API"""
    
    def __init__(self, api_url: str = None, api_key: str = None):
        self.api_url = api_url or BlogConfig.GROK_API_URL
        self.api_key = api_key or BlogConfig.GROK_API_KEY
        self.session = requests.Session()
        # Disable proxies for local gateway connection
        self.session.trust_env = False
        self.session.proxies = {"http": None, "https": None}
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        })
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]] | Dict[str, Any],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request to Grok
        """
        # If first argument is a full payload dict, use it
        if isinstance(messages, dict) and "messages" in messages:
            payload = messages
            # Ensure model is set if missing
            if "model" not in payload:
                payload["model"] = model or BlogConfig.GROK_MODEL
        else:
            # Build payload from separate args
            model = model or BlogConfig.GROK_MODEL
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream
            }
            # Add extra params (like response_format)
            payload.update(kwargs)
        
        if True: # Always log payload for debugging
            import json
            logger.info(f"Sending payload to Grok: {json.dumps(payload, default=str)}")
            
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries + 1):
            try:
                response = self.session.post(self.api_url, json=payload)
                
                # If success, return immediately
                if response.status_code == 200:
                    return response.json()
                
                # If server error (500-599), retry to trigger token rotation
                if 500 <= response.status_code < 600:
                    logger.warning(f"Grok API Server Error ({response.status_code}). Retrying ({attempt+1}/{max_retries}) to switch token...")
                    import time
                    time.sleep(retry_delay)
                    continue
                
                # If other error (4xx), raise immediately
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Grok API Connection Error: {e}")
                if attempt < max_retries:
                    logger.info("Retrying...")
                    import time
                    time.sleep(retry_delay)
                else:
                    raise
    
    def rewrite_content(
        self,
        original_content: str,
        keyword: str,
        category: str,
        min_words: int = 1500,
        max_words: int = 3000
    ) -> Dict[str, Any]:
        """
        Rewrite content using Grok AI
        
        Args:
            original_content: Original article content
            keyword: Main keyword for SEO
            category: Article category
            min_words: Minimum word count
            max_words: Maximum word count
        
        Returns:
            Dict with rewritten content and metadata
        """
        from blog_config import CONTENT_REWRITE_PROMPT
        
        prompt = CONTENT_REWRITE_PROMPT.format(
            original_content=original_content,
            keyword=keyword,
            category=category,
            min_words=min_words,
            max_words=max_words
        )
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert content writer and SEO specialist. CRITICAL: YOU MUST OUTPUT ONLY VALID JSON. DO NOT WRITE ANY INTRODUCTORY TEXT. DO NOT EXPLAIN. START IMMEDIATELY WITH { AND END WITH }."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Enable JSON mode for stability
        payload = {
            "messages": messages,
            "temperature": 0.5,  # Lower temperature for strict formatting
            "max_tokens": 4000,
            "response_format": {"type": "json_object"}
        }
        
        logger.info(f"Rewriting content for keyword: {keyword}")
        response = self.chat_completion(payload)
        
        # Extract content from response
        if 'choices' in response and len(response['choices']) > 0:
            content_text = response['choices'][0]['message']['content']
        else:
            logger.error(f"Unexpected response format: {response}")
            return None
        
        # Parse JSON from response
        try:
            # 1. Clean markdown code blocks
            if "```" in content_text:
                import re
                match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content_text)
                if match:
                    content_text = match.group(1)
            
            # 2. Find JSON boundaries (start with { and end with })
            content_text = content_text.strip()
            start_idx = content_text.find('{')
            end_idx = content_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                content_text = content_text[start_idx:end_idx+1]
            
            content_data = json.loads(content_text)
            logger.info(f"Successfully rewrote content: {content_data.get('title', 'Unknown')}")
            return content_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text start: {content_text[:200]}...")
            # Fallback or return None to retry
            return None
    
    def generate_image(
        self,
        topic: str,
        mood: str = "professional and engaging",
        elements: str = "relevant to the topic"
    ) -> str:
        """
        Generate image using Grok AI
        
        Args:
            topic: Image topic/subject
            mood: Desired mood/style
            elements: Elements to include
        
        Returns:
            Image URL or base64 data
        """
        from blog_config import IMAGE_GENERATION_PROMPT
        
        prompt = IMAGE_GENERATION_PROMPT.format(
            topic=topic,
            mood=mood,
            elements=elements
        )
        
        messages = [
            {
                "role": "user",
                "content": f"Draw: {prompt}"
            }
        ]
        
        logger.info(f"Generating image for topic: {topic}")
        response = self.chat_completion(
            messages,
            model=BlogConfig.GROK_IMAGE_MODEL,
            temperature=0.9
        )
        
        # Extract image URL from response
        content = response['choices'][0]['message']['content']
        
        # Grok returns image in markdown format: ![](url)
        if "![" in content and "](" in content:
            start = content.find("](") + 2
            end = content.find(")", start)
            image_url = content[start:end]
            logger.info(f"Generated image URL: {image_url}")
            return image_url
        
        logger.warning("No image URL found in response")
        return ""
    
    def generate_schema(
        self,
        title: str,
        description: str,
        category: str,
        date: str,
        author: str,
        image_url: str,
        article_url: str
    ) -> Dict[str, Any]:
        """
        Generate Schema.org markup using Grok AI
        
        Args:
            title: Article title
            description: Article description
            category: Article category
            date: Publication date (ISO format)
            author: Author name
            image_url: Featured image URL
            article_url: Full article URL
        
        Returns:
            Schema.org JSON-LD dict
        """
        from blog_config import SEO_SCHEMA_TEMPLATE
        
        prompt = SEO_SCHEMA_TEMPLATE.format(
            title=title,
            description=description,
            category=category,
            date=date,
            author=author,
            image_url=image_url,
            article_url=article_url
        )
        
        messages = [
            {
                "role": "system",
                "content": "You are an SEO expert specializing in Schema.org structured data markup."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        logger.info(f"Generating schema for: {title}")
        response = self.chat_completion(messages, temperature=0.3)
        
        content_text = response['choices'][0]['message']['content']
        
        # Parse JSON
        try:
            if "```json" in content_text:
                json_start = content_text.find("```json") + 7
                json_end = content_text.find("```", json_start)
                content_text = content_text[json_start:json_end].strip()
            elif "```" in content_text:
                json_start = content_text.find("```") + 3
                json_end = content_text.find("```", json_start)
                content_text = content_text[json_start:json_end].strip()
            
            schema_data = json.loads(content_text)
            logger.info("Successfully generated schema markup")
            return schema_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse schema JSON: {e}")
            # Return basic schema as fallback
            return self._get_basic_schema(
                title, description, category, date, author, image_url, article_url
            )
    
    def _get_basic_schema(
        self,
        title: str,
        description: str,
        category: str,
        date: str,
        author: str,
        image_url: str,
        article_url: str
    ) -> Dict[str, Any]:
        """Generate basic schema markup as fallback"""
        return {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": title,
            "description": description,
            "image": image_url,
            "datePublished": date,
            "dateModified": date,
            "author": {
                "@type": "Person",
                "name": author
            },
            "publisher": {
                "@type": "Organization",
                "name": BlogConfig.SITE_NAME,
                "logo": {
                    "@type": "ImageObject",
                    "url": f"{BlogConfig.SITE_URL}/assets/logo.png"
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": article_url
            }
        }


# Test function
if __name__ == "__main__":
    client = GrokClient()
    
    # Test rewrite
    test_content = """
    Jakarta - Teknologi AI semakin berkembang pesat. 
    Banyak perusahaan mulai mengadopsi AI untuk meningkatkan produktivitas.
    """
    
    result = client.rewrite_content(
        original_content=test_content,
        keyword="teknologi AI",
        category="teknologi"
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

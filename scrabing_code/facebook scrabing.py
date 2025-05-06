import os
import time
import logging
import requests
import re
from io import BytesIO
from urllib.parse import urlparse
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from typing import List, Dict
import json
from pathlib import Path
from django.conf import settings
import spacy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scraper.log'
)
logger = logging.getLogger(__name__)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Configuration class
class ScraperConfig:
    CHROME_DRIVER_PATH = os.path.join(settings.BASE_DIR, "sentiment", "chromedriver.exe")
    MEDIA_FOLDER = "media"
    MIN_RESOLUTION = (150, 150)
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 10
    STOPWORDS = {
        "account", "verify", "forget", "forgotten", "forgot", "reply", "like", "password",
        "login", "log", "sign", "signed", "signing", "access", "verify", "verified", "verification",
        "connect", "connection", "connecting", "share", "shared", "sharing", "update", "updated",
        "message", "messages", "messaging", "follow", "following", "follower", "followers",
        "logout", "signin", "signup", "email", "username", "register", "remember", "recover"
    }

class SocialMediaScraper:
    def __init__(self, config: ScraperConfig = ScraperConfig()):
        self.config = config
        self.driver = None
        self.setup_driver()

    def setup_driver(self) -> None:
        """Initialize Chrome WebDriver with configured options."""
        try:
            options = ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920x1080")
            service = ChromeService(self.config.CHROME_DRIVER_PATH)
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise

    def filter_short_words(self, text: str) -> str:
        """Filter out short words, numbers, mixed alphanumeric patterns, sensitive keywords, and person names."""
        try:
            # Detect named entities
            doc = nlp(text)
            names_to_remove = {ent.text for ent in doc.ents if ent.label_ == "PERSON"}

            words = text.split()
            filtered_words = []
            for word in words:
                clean_word = word.lower().strip(".,!?:;\"'()[]{}")
                if (len(clean_word) <= 1 or
                    re.match(r'^[a-zA-Z]\d+$', clean_word) or
                    re.match(r'^\d+[a-zA-Z]$', clean_word) or
                    re.match(r'^\d+$', clean_word) or
                    clean_word in self.config.STOPWORDS or
                    word in names_to_remove):
                    continue
                filtered_words.append(word)
            return ' '.join(filtered_words)
        except Exception as e:
            logger.error(f"Error filtering text: {str(e)}")
            return text

    def remove_duplicate_phrases(self, texts: List[str], window_size: int = 4) -> List[str]:
        """Remove duplicate phrases from a list of texts using a sliding window approach."""
        try:
            seen_phrases = set()
            deduplicated_texts = []
            
            for text in texts:
                words = text.split()
                if len(words) < window_size:
                    if text not in seen_phrases:
                        deduplicated_texts.append(text)
                        seen_phrases.add(text)
                    continue
                
                phrases = [' '.join(words[i:i+window_size]) 
                         for i in range(len(words) - window_size + 1)]
                
                is_unique = True
                for phrase in phrases:
                    if phrase in seen_phrases:
                        is_unique = False
                        break
                
                if is_unique:
                    deduplicated_texts.append(text)
                    for phrase in phrases:
                        seen_phrases.add(phrase)
            
            logger.info(f"Removed duplicates, reduced from {len(texts)} to {len(deduplicated_texts)} texts")
            return deduplicated_texts
        except Exception as e:
            logger.error(f"Error removing duplicate phrases: {str(e)}")
            return texts

    def clear_download_folder(self) -> None:
        """Clear the media download folder."""
        folder_path = Path(self.config.MEDIA_FOLDER)
        try:
            folder_path.mkdir(exist_ok=True)
            for file in folder_path.iterdir():
                if file.is_file():
                    file.unlink()
            logger.info(f"Cleared download folder: {self.config.MEDIA_FOLDER}")
        except Exception as e:
            logger.error(f"Failed to clear download folder: {str(e)}")

    def save_image(self, image_url: str) -> bool:
        """Save image from URL if it meets minimum resolution requirements."""
        folder_path = Path(self.config.MEDIA_FOLDER)
        image_name = urlparse(image_url).path.split('/')[-1].split('?')[0]
        if not image_name.lower().endswith(".jpg"):
            image_name = image_name.split('.')[0] + ".jpg"
        
        image_path = folder_path / image_name

        if image_path.exists() or re.match(r'^\d[a-zA-Z].*', image_name.lower()):
            return False

        for attempt in range(self.config.MAX_RETRIES):
            try:
                response = requests.get(
                    image_url, 
                    stream=True, 
                    timeout=self.config.REQUEST_TIMEOUT
                )
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content)).convert("RGB")
                    if (image.size[0] < self.config.MIN_RESOLUTION[0] or 
                        image.size[1] < self.config.MIN_RESOLUTION[1]):
                        return False
                    image.save(image_path, "JPEG")
                    logger.info(f"Saved image: {image_name}")
                    return True
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {image_url}: {str(e)}")
                if attempt == self.config.MAX_RETRIES - 1:
                    logger.error(f"Failed to save image after retries: {image_url}")
                    return False
        return False

    def identify_platform(self, url: str) -> str:
        """Identify the social media platform from URL."""
        domain = urlparse(url).netloc.lower()
        platforms = {
            "facebook": "facebook",
            "instagram": "instagram",
            "tiktok": "tiktok",
            "twitter": "x",
            "x.com": "x"
        }
        for key, platform in platforms.items():
            if key in domain:
                return platform
        return "generic"

    def extract_post_and_comment_text(self) -> List[str]:
        """Extract relevant text from posts and comments."""
        texts = []
        try:
            for tag in ["div", "p", "span", "section"]:
                elements = self.driver.find_elements(By.TAG_NAME, tag)
                for elem in elements:
                    text = elem.text.strip()
                    if (text and len(text.split()) > 3 and 
                        not any(word in text.lower() for word in self.config.STOPWORDS)):
                        texts.append(text)
            logger.info(f"Extracted {len(texts)} text elements")
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
        return texts

    def scroll_and_extract(self, target_images: int, max_minutes: float) -> List[str]:
        """Scroll page and extract images and text."""
        body = self.driver.find_element(By.TAG_NAME, "body")
        seen_imgs = set()
        all_texts = []
        start_time = time.time()

        while len(os.listdir(self.config.MEDIA_FOLDER)) < target_images:
            try:
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(2)

                for elem in self.driver.find_elements(By.TAG_NAME, "img"):
                    src = elem.get_attribute("src")
                    if src and src.startswith("http") and src not in seen_imgs:
                        if self.save_image(src):
                            seen_imgs.add(src)

                all_texts.extend(self.extract_post_and_comment_text())

                if (time.time() - start_time) / 60 >= max_minutes:
                    logger.info("Reached maximum time limit")
                    break

            except Exception as e:
                logger.error(f"Error during scrolling: {str(e)}")
                break

        return all_texts

    def rearrange_images(self) -> List[Dict]:
        """Rearrange images by size and return metadata."""
        folder_path = Path(self.config.MEDIA_FOLDER)
        images = []
        
        try:
            for file in folder_path.iterdir():
                if file.suffix.lower() == ".jpg":
                    with Image.open(file) as img:
                        w, h = img.size
                        images.append((file.name, w, h, w * h))

            images.sort(key=lambda x: x[3], reverse=True)
            metadata = []
            
            for i, (name, w, h, _) in enumerate(images):
                new_name = f"image_{i+1}.jpg"
                os.rename(folder_path / name, folder_path / new_name)
                metadata.append({
                    "filename": new_name,
                    "width": w,
                    "height": h,
                    "area": w * h
                })
                
            logger.info(f"Rearranged {len(metadata)} images")
            return metadata
        except Exception as e:
            logger.error(f"Error rearranging images: {str(e)}")
            return []

    def extract_social_media_data(self, url: str, target_images: int = 3) -> Dict:
        """Main method to extract social media data with deduplicated phrases."""
        try:
            self.clear_download_folder()
            platform = self.identify_platform(url)
            logger.info(f"Scraping {platform} URL: {url}")

            self.driver.get(url)
            time.sleep(5)

            all_raw_texts = self.scroll_and_extract(
                target_images, 
                max_minutes=target_images * 0.25
            )

            filtered_texts = [
                self.filter_short_words(txt) 
                for txt in all_raw_texts 
                if txt.strip()
            ]

            deduplicated_texts = self.remove_duplicate_phrases(filtered_texts)
            combined_text = " ".join(deduplicated_texts)
            image_data = self.rearrange_images()

            result = {
                "platform": platform,
                "texts": deduplicated_texts,
                "combined_text": combined_text,
                "image_folder": self.config.MEDIA_FOLDER,
                "image_count": len(image_data),
                "images": image_data
            }

            with open('scraper_results.json', 'w') as f:
                json.dump(result, f, indent=2)
                
            logger.info("Data extraction completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error in extract_social_media_data: {str(e)}")
            return {}
        finally:
            try:
                self.driver.quit()
            except:
                pass

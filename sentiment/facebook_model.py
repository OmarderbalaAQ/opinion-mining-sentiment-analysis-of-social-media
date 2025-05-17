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
from typing import List, Dict, Optional, Tuple
import json
from pathlib import Path

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.path.join(log_dir, 'scraper.log')
)
logger = logging.getLogger(__name__)

# Configuration class
class ScraperConfig:
    CHROME_DRIVER_PATH = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
    MEDIA_FOLDER = "media"
    MIN_RESOLUTION = (150, 150)
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 10
    STOPWORDS = {
        "account", "verify", "forget", "forgotten", "forgot", "reply", "like", "password",
        "login", "log", "sign", "signed", "signing", "access", "verify", "verified", "verification",
        "connect", "connection", "connecting", "share", "shared", "sharing", "update", "updated",
        "message", "messages", "messaging", "follow", "following", "follower", "followers"
    }

class SocialMediaScraper:
    def __init__(self, config: ScraperConfig = ScraperConfig()):
        self.config = config
        self.setup_driver()
        
    def setup_driver(self) -> None:
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
        words = text.split()
        filtered_words = [
            word for word in words
            if len(word) > 1 and 
            not re.match(r'^[a-zA-Z0-9]+$', word) or 
            not (any(c.isdigit() for c in word) and any(c.isalpha() for c in word)) and
            not word.isdigit()
        ]
        return ' '.join(filtered_words)

    def remove_duplicate_phrases(self, texts: List[str], window_size: int = 4) -> List[str]:
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
        folder_path = Path(self.config.MEDIA_FOLDER)
        base_name = urlparse(image_url).path.split('/')[-1].split('?')[0]
        if not base_name.lower().endswith(".jpg"):
            base_name = base_name.split('.')[0]
        image_name = f"{base_name}_{int(time.time())}.jpg"
        image_path = folder_path / image_name

        if image_path.exists():
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
        domain = urlparse(url).netloc.lower()
        platforms = {
            "facebook": "facebook",
            "instagram": "instagram",
            "tiktok": "tiktok",
            "twitter": "twitter",
            "x.com": "twitter"
        }
        for key, platform in platforms.items():
            if key in domain:
                return platform
        return "generic"

    def extract_post_and_comment_text(self) -> List[str]:
        texts = []
        try:
            selectors = [
                (By.XPATH, "//div[contains(@class, 'x1yztbdb')]//div[@dir='auto']"),
                (By.XPATH, "//div[contains(@class, 'x1n2onr6')]//span[@dir='auto']")
            ]
            for selector_type, selector in selectors:
                elements = self.driver.find_elements(selector_type, selector)
                texts.extend([elem.text.strip() for elem in elements if elem.text.strip()])
            logger.info(f"Extracted {len(texts)} text elements")
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
        return texts

    def scroll_and_extract(self, target_images: int, max_minutes: float) -> List[str]:
        body = self.driver.find_element(By.TAG_NAME, "body")
        seen_imgs = set()
        all_texts = []
        start_time = time.time()

        while len(os.listdir(self.config.MEDIA_FOLDER)) < target_images:
            try:
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(2)

                # Extract images
                for elem in self.driver.find_elements(By.TAG_NAME, "img"):
                    src = elem.get_attribute("src")
                    if src and src not in seen_imgs:
                        if self.save_image(src):
                            seen_imgs.add(src)

                # Extract texts
                all_texts.extend(self.extract_post_and_comment_text())

                # Check time limit
                if (time.time() - start_time) / 60 >= max_minutes:
                    logger.info("Reached maximum time limit")
                    break

            except Exception as e:
                logger.error(f"Error during scrolling: {str(e)}")
                break

        return all_texts

    def rearrange_images(self) -> List[str]:
        """Rearrange images by size and return list of paths."""
        folder_path = Path(self.config.MEDIA_FOLDER)
        images = []
        
        try:
            for file in folder_path.iterdir():
                if file.suffix == ".jpg":
                    with Image.open(file) as img:
                        w, h = img.size
                        images.append((file.name, w, h, w * h))

            images.sort(key=lambda x: x[3], reverse=True)
            image_paths = []
            
            for i, (name, w, h, _) in enumerate(images):
                new_name = f"image_{i+1}.jpg"
                os.rename(folder_path / name, folder_path / new_name)
                image_paths.append(str(folder_path / new_name))
                
            logger.info(f"Rearranged {len(image_paths)} images")
            return image_paths
        except Exception as e:
            logger.error(f"Error rearranging images: {str(e)}")
            return []

    def extract_social_media_data(self, url: str, target_images: int = 3) -> Dict:
        try:
            self.clear_download_folder()
            platform = self.identify_platform(url)
            if platform != "facebook":
                logger.error(f"URL {url} is not a Facebook URL")
                return {}
            logger.info(f"Scraping {platform} URL: {url}")

            self.driver.get(url)
            time.sleep(5)

            all_raw_texts = self.scroll_and_extract(
                target_images,
                max_minutes=target_images * 0.25
            )

            # Filter short words
            filtered_texts = [
                self.filter_short_words(txt)
                for txt in all_raw_texts
                if txt.strip()
            ]

            # Remove duplicate phrases
            deduplicated_texts = self.remove_duplicate_phrases(filtered_texts)

            # Combine deduplicated texts into post_text
            post_text = " ".join(deduplicated_texts) if deduplicated_texts else ""
            image_path = self.rearrange_images()[0] if self.rearrange_images() else None

            result = {
                "post_text": post_text,
                "image_path": image_path
            }

            # Save results to JSON (optional, for debugging)
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
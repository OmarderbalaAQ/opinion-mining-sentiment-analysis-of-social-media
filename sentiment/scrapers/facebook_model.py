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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from django.conf import settings

class ScraperConfig:
    CHROME_DRIVER_PATH = getattr(settings, 'CHROME_DRIVER_EXECUTABLE_PATH', None)
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    MEDIA_FOLDER = os.path.join(PROJECT_ROOT, "media")
    MIN_RESOLUTION = (150, 150)
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 10
    STOPWORDS = {
        "account", "verify", "forget", "forgotten", "forgot", "reply", "like", "password",
        "login", "log", "sign", "signed", "signing", "access", "verified", "verification",
        "connect", "connection", "connecting", "share", "shared", "sharing", "update", "updated",
        "message", "messages", "messaging", "follow", "following", "follower", "followers"
    }

    def __init__(self):
        os.makedirs(self.MEDIA_FOLDER, exist_ok=True)

class SocialMediaScraper:
    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config if config else ScraperConfig()
        self.driver = None
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def clear_media_folder(self):
        if os.path.exists(self.config.MEDIA_FOLDER):
            for file in os.listdir(self.config.MEDIA_FOLDER):
                path = os.path.join(self.config.MEDIA_FOLDER, file)
                if os.path.isfile(path):
                    try:
                        os.remove(path)
                    except Exception as e:
                        self.logger.warning(f"Failed to delete {path}: {e}")

    def setup_driver(self):
        if self.driver:
            return
        options = ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        try:
            service = ChromeService(self.config.CHROME_DRIVER_PATH)
            self.driver = webdriver.Chrome(service=service, options=options)
            self.logger.info("ChromeDriver initialized")
        except Exception as e:
            self.logger.error(f"ChromeDriver initialization failed: {e}")
            raise

    def close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("ChromeDriver closed")
            except Exception as e:
                self.logger.error(f"Error closing driver: {e}")
            self.driver = None

    def filter_text(self, text: str) -> str:
        text = text.strip()
        if not text:
            return ""
        patterns = [
            r"view all \d+ (replies|comments)",
            r"(\d+k|\d+)\s+(comments|shares|likes)",
            r"^\d+[mhd]$",
            r"see more|read more"
        ]
        for pattern in patterns:
            if re.search(pattern, text.lower()):
                return ""
        if (any(word in text.lower() for word in self.config.STOPWORDS) or
            (len(text.split()) < 3 and not any(c.isalpha() for c in text))):
            return ""
        return text

    def save_image(self, image_url: str) -> Optional[str]:
        for attempt in range(self.config.MAX_RETRIES):
            try:
                response = requests.get(image_url, timeout=self.config.REQUEST_TIMEOUT)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
                if img.size[0] < self.config.MIN_RESOLUTION[0] or img.size[1] < self.config.MIN_RESOLUTION[1]:
                    return None
                filename = f"fb_{int(time.time()*1000)}.jpg"
                path = os.path.join(self.config.MEDIA_FOLDER, filename)
                img.convert("RGB").save(path, "JPEG")
                return path
            except Exception as e:
                self.logger.warning(f"Image download failed (attempt {attempt+1}): {e}")
                time.sleep(1)
        return None

    def extract_text_elements(self) -> List[str]:
        selectors = [
            (By.XPATH, "//div[contains(@class, 'x1yztbdb')]//div[@dir='auto']"),
            (By.XPATH, "//div[@role='article']//div[@data-testid='post-message']"),
            (By.XPATH, "//div[contains(@aria-label, 'Comment')]//div[@dir='auto']"),
        ]
        texts = []
        for by, selector in selectors:
            try:
                elements = self.driver.find_elements(by, selector)
                texts.extend([e.text.strip() for e in elements if e.text.strip()])
            except Exception as e:
                self.logger.debug(f"Selector failed: {selector} - {e}")
        return texts

    def scroll_and_collect(self, target_images: int, timeout: float = 2.0) -> Tuple[List[str], List[str]]:
        start_time = time.time()
        seen_texts = set()
        seen_images = set()
        collected_texts = []
        collected_images = []

        while len(collected_images) < target_images and (time.time() - start_time) < timeout * 60:
            try:
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                time.sleep(2)

                new_texts = [t for t in self.extract_text_elements() if t not in seen_texts]
                collected_texts.extend(new_texts)
                seen_texts.update(new_texts)

                for img in self.driver.find_elements(By.TAG_NAME, 'img'):
                    src = img.get_attribute('src')
                    if src and src.startswith('http') and src not in seen_images:
                        path = self.save_image(src)
                        if path:
                            collected_images.append(path)
                            seen_images.add(src)
                            if len(collected_images) >= target_images:
                                break
            except Exception as e:
                self.logger.error(f"Error during scrolling: {e}")
                break

        return collected_texts, collected_images

    def format_post_and_comments(self, texts: List[str]) -> str:
        if not texts:
            return ""
        post = f"Post: {texts[0]}"
        comments = [
            f"Comment {i}: {text}"
            for i, text in enumerate(texts[1:14], start=1)
        ]
        return post + "\n" + "\n".join(comments)

    def extract_social_media_data(self, url: str) -> Dict:
        self.clear_media_folder()
        self.setup_driver()
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)

            texts, images = self.scroll_and_collect(target_images=1)
            filtered_texts = [self.filter_text(t) for t in texts if t]
            unique_texts = list(dict.fromkeys(filtered_texts))

            return {
                "post_text": self.format_post_and_comments(unique_texts) if unique_texts else "",
                "image_path": os.path.join("media", os.path.basename(images[0])) if images else None,
                "error": None
            }
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            return {
                "post_text": "",
                "image_path": None,
                "error": str(e)
            }
        finally:
            self.close_driver()

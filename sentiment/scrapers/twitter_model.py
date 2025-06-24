import os
import time
import logging
import requests
from io import BytesIO
from typing import List, Dict, Optional
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from urllib.parse import urlparse

# إعداد المسارات
BASE_DIR = os.path.dirname(__file__)
chrome_path = os.path.join(BASE_DIR, "chromedriver.exe")
MEDIA_FOLDER = os.path.join(BASE_DIR, "media")
LOG_FOLDER = os.path.join(BASE_DIR, "logs")
os.makedirs(MEDIA_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

# بيانات تسجيل الدخول
TWITTER_USERNAME = "moatazabdo865"
TWITTER_PASSWORD = "Abdo2244"

# إعدادات اللوج
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_FOLDER, "twitter_scraper.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TwitterScraperConfig:
    MEDIA_FOLDER = MEDIA_FOLDER
    MIN_RESOLUTION = (150, 150)
    REQUEST_TIMEOUT = 10
    MAX_WAIT = 20
    USERNAME = TWITTER_USERNAME
    PASSWORD = TWITTER_PASSWORD
    CHROME_PATH = chrome_path

class TwitterScraper:
    def __init__(self, config: TwitterScraperConfig = TwitterScraperConfig()):
        self.config = config
        self.driver = None
        self.wait = None

    def setup_driver(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        service = Service(executable_path=self.config.CHROME_PATH)
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, self.config.MAX_WAIT)
        logger.info("Chrome WebDriver initialized")

    def _ensure_driver(self):
        if not self.driver:
            self.setup_driver()

    def close_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
            self.driver = None

    def login(self) -> bool:
        try:
            self.driver.get("https://x.com/login")
            username_input = self.wait.until(EC.presence_of_element_located((By.NAME, "text")))
            username_input.send_keys(self.config.USERNAME)
            username_input.send_keys(Keys.RETURN)
            time.sleep(2)
            password_input = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))
            password_input.send_keys(self.config.PASSWORD)
            password_input.send_keys(Keys.RETURN)
            self.wait.until(EC.presence_of_element_located((By.XPATH, '//nav')))
            logger.info("[✓] تم تسجيل الدخول بنجاح.")
            return True
        except Exception as e:
            logger.warning(f"[!] فشل تسجيل الدخول: {e}")
            return False

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

    def clean_text(self, text: str) -> str:
        text = text.strip()
        if len(text) < 10:
            return ""
        return text

    def extract_social_media_data(self, url: str, target_images: int = 1) -> Dict:
        self._ensure_driver()
        self.login()
        self.driver.get(url)
        time.sleep(5)
        if "/hashtag/" in url or "search?q=%23" in url:
            return self._extract_from_hashtag(limit=target_images)
        else:
            return self._extract_from_tweet(limit=target_images)

    def _extract_from_tweet(self, limit: int = 1) -> Dict:
        texts, images, seen_texts = [], [], set()
        try:
            tweet_elem = self.wait.until(EC.presence_of_element_located((By.XPATH, '//div[@data-testid="tweetText"]')))
            main_text = self.clean_text(tweet_elem.text)
            if main_text:
                texts.append(main_text)
                seen_texts.add(main_text)
        except Exception as e:
            logger.warning(f"Tweet text not found: {e}")

        try:
            img_elements = self.driver.find_elements(By.XPATH, '//img[contains(@src, "twimg.com/media")]')
            for img in img_elements:
                src = img.get_attribute("src")
                saved = self.save_image(src)
                if saved:
                    images.append(saved)
                if len(images) >= limit:
                    break
        except Exception as e:
            logger.warning(f"Image download error: {e}")

        last_height = self.driver.execute_script("return document.body.scrollHeight")
        reply_count = 0
        reply_attempts = 0
        while len(texts) < limit + 13 and reply_attempts < 10:
            tweet_divs = self.driver.find_elements(By.XPATH, '//div[@data-testid="cellInnerDiv"]')
            for div in tweet_divs:
                try:
                    text_elem = div.find_element(By.XPATH, './/div[@data-testid="tweetText"]')
                    reply_text = self.clean_text(text_elem.text)
                    if reply_text and reply_text not in seen_texts:
                        texts.append(reply_text)
                        seen_texts.add(reply_text)
                        reply_count += 1
                        img_elements = div.find_elements(By.XPATH, './/img[contains(@src, "twimg.com/media")]')
                        for img in img_elements:
                            src = img.get_attribute("src")
                            filename = f"reply{reply_count}.jpg"
                            self.save_image(src, filename)
                            logger.info(f"Reply image saved: {filename}")
                        if len(texts) >= limit + 13:
                            break
                except:
                    continue
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            reply_attempts += 1
        return {
            "text_list": texts,
            "image_path": images[0] if images else None
        }

    def _extract_from_hashtag(self, limit: int = 5) -> Dict:
        texts, images, seen = [], [], set()
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while len(texts) < limit:
            tweet_divs = self.driver.find_elements(By.XPATH, '//div[@data-testid="cellInnerDiv"]')
            for div in tweet_divs:
                try:
                    text_elem = div.find_element(By.XPATH, './/div[@data-testid="tweetText"]')
                    text = self.clean_text(text_elem.text)
                    if text and text not in seen:
                        texts.append(text)
                        seen.add(text)
                    img_elements = div.find_elements(By.XPATH, './/img[contains(@src, "twimg.com/media")]')
                    for img in img_elements:
                        src = img.get_attribute("src")
                        saved = self.save_image(src)
                        if saved:
                            images.append(saved)
                    if len(texts) >= limit:
                        break
                except:
                    continue
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        return {
            "text_list": texts,
            "image_path": images[0] if images else None
        }

# ✅ واجهات مبسطة لدعم Django
scraper_instance = TwitterScraper()

def twitter_login():
    scraper_instance._ensure_driver()
    scraper_instance.login()

def extract_from_tweet(url: str) -> Optional[Dict]:
    data = scraper_instance.extract_social_media_data(url)
    scraper_instance.close_driver()
    if data:
        return {
            "post_text": data["text_list"][0] if data["text_list"] else "",
            "comments": data["text_list"][1:] if len(data["text_list"]) > 1 else [],
            "image_path": data["image_path"]
        }
    return None

def extract_from_hashtag(url: str, limit: int = 5) -> Optional[List[Dict]]:
    data = scraper_instance.extract_social_media_data(url, target_images=limit)
    scraper_instance.close_driver()
    if data:
        return [{"text": t} for t in data["text_list"]]
    return []

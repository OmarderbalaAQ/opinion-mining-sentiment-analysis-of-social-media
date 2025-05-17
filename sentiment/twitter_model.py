from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='twitter_scraper.log'
)
logger = logging.getLogger(__name__)

# بيانات الدخول من بيئة المتغيرات
USERNAME = os.getenv('TWITTER_USERNAME', 'default_username')
PASSWORD = os.getenv('TWITTER_PASSWORD', 'default_password')

# إعداد مجلد الصور
if not os.path.exists("media"):
    os.makedirs("media")

# إعداد المتصفح Chrome بوضع headless
chrome_path = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
service = Service(executable_path=chrome_path)
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 20)

# دالة تسجيل الدخول
def twitter_login():
    try:
        driver.get("https://x.com/login")
        username_input = wait.until(EC.presence_of_element_located((By.NAME, "text")))
        username_input.send_keys(USERNAME)
        username_input.send_keys(Keys.RETURN)
        time.sleep(2)

        password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_input.send_keys(PASSWORD)
        password_input.send_keys(Keys.RETURN)

        wait.until(EC.presence_of_element_located((By.XPATH, '//nav')))
        logger.info("[✓] تم تسجيل الدخول بنجاح.")
        return True
    except Exception as e:
        logger.error(f"[!] فشل تسجيل الدخول: {str(e)}. سيتم المتابعة بدون تسجيل دخول.")
        return False

# استخراج من تغريدة
def extract_from_tweet(tweet_url):
    driver.get(tweet_url)
    time.sleep(5)

    texts = []
    image_paths = []

    try:
        tweet_text_elem = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@data-testid="tweetText"]')))
        texts.append(tweet_text_elem.text.strip())
    except Exception as e:
        logger.error(f"[✗] خطأ أثناء استخراج النص: {str(e)}")

    try:
        image_elements = driver.find_elements(By.XPATH, '//img[contains(@src, "twimg.com/media")]')
        for idx, img in enumerate(image_elements):
            src = img.get_attribute('src')
            img_data = requests.get(src).content
            filename = os.path.join("media", f"tweet_image_{int(time.time())}_{idx+1}.jpg")
            with open(filename, 'wb') as f:
                f.write(img_data)
            image_paths.append(filename)
    except Exception as e:
        logger.error(f"[!] لم يتم استخراج صور: {str(e)}")

    return {
        "post_text": " ".join(texts) if texts else "",
        "image_path": image_paths[0] if image_paths else None
    }

# استخراج من هاشتاج
def extract_from_hashtag(hashtag_url, limit=5):
    driver.get(hashtag_url)
    time.sleep(5)

    texts = []
    image_paths = []
    seen = set()
    last_height = driver.execute_script("return document.body.scrollHeight")

    while len(texts) < limit:
        tweet_divs = driver.find_elements(By.XPATH, '//div[@data-testid="cellInnerDiv" and contains(@class, "css-1dbjc4n")]')
        for div in tweet_divs:
            try:
                tweet_text_elem = div.find_element(By.XPATH, './/div[@data-testid="tweetText"]')
                tweet_text = tweet_text_elem.text.strip()
                if tweet_text not in seen:
                    seen.add(tweet_text)
                    texts.append(tweet_text)

                image_elements = div.find_elements(By.XPATH, './/img[contains(@src, "twimg.com/media")]')
                for idx, img in enumerate(image_elements):
                    src = img.get_attribute('src')
                    img_data = requests.get(src).content
                    filename = os.path.join("media", f"hashtag_image_{int(time.time())}_{len(texts)}_{idx+1}.jpg")
                    with open(filename, 'wb') as f:
                        f.write(img_data)
                    image_paths.append(filename)

                if len(texts) >= limit:
                    break
            except:
                continue

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    return {
        "post_text": " ".join(texts) if texts else "",
        "image_path": image_paths[0] if image_paths else None
    }
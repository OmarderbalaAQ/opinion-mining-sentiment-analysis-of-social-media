import os
import time
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
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
from django.conf import settings

# Load stopwords once
stop_words = set(stopwords.words('english'))

# Set up Chrome driver (headless)
CHROME_DRIVER_PATH = os.path.join(settings.BASE_DIR, "sentiment", "chromedriver.exe")
chrome_options = ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
service = ChromeService(CHROME_DRIVER_PATH)

# Clean and tokenize text
def text_clean(text):
    nopunc = ''.join([char.lower() for char in text if char not in string.punctuation])
    tokens = word_tokenize(nopunc)
    return ' '.join([word for word in tokens if word not in stop_words])

# Clear existing images
def clear_download_folder(folder="media"):
    if os.path.exists(folder):
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

# Save image from URL
def save_image(image_url, folder="media"):
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    image_name = image_url.split("/")[-1].split("?")[0]
    if not image_name.lower().endswith(".jpg"):
        image_name = image_name.split('.')[0] + ".jpg"
    
    image_path = os.path.join(folder, image_name)

    if os.path.exists(image_path):
        return False
    if re.match(r'^\d[a-zA-Z].*', image_name.lower()):  # Skip images with number + letter at the start
        return False

    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content)).convert("RGB")
            image.save(image_path, "JPEG")
            return True
    except:
        return False
    return False

# Extract visible text elements
def extract_text_from_elements(driver, tag="div"):
    return [elem.text.strip() for elem in driver.find_elements(By.TAG_NAME, tag) if elem.text.strip()]

# Scroll and collect text/images
def scroll_and_extract(driver, target_images=3):
    body = driver.find_element(By.TAG_NAME, "body")
    texts = []
    while len(os.listdir("media")) < target_images:
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(2)
        texts.extend(extract_text_from_elements(driver))
        for img in driver.find_elements(By.TAG_NAME, "img"):
            if len(os.listdir("media")) >= target_images:
                break
            img_url = img.get_attribute("src")
            if img_url and img_url.startswith("http"):
                save_image(img_url)
    return texts

# Identify platform from URL
def identify_platform(url):
    domain = urlparse(url).netloc.lower()
    if "facebook" in domain:
        return "facebook"
    elif "instagram" in domain:
        return "instagram"
    elif "twitter" in domain or "x.com" in domain:
        return "x"
    return "generic"

# Main scraping interface
def extract_social_media_data(url, target_images=3):
    clear_download_folder()  # Clear the media folder before starting
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)
    time.sleep(5)  # Wait for the page to load
    texts = scroll_and_extract(driver, target_images)  # Scroll and extract text/images
    driver.quit()
    
    # Clean the texts and remove duplicates
    cleaned_texts = [text_clean(t) for t in texts]
    cleaned_texts = list(set(cleaned_texts))  # Remove duplicates by converting to a set

    combined_text = " ".join(cleaned_texts)  # Combine all texts into one string

    return {
        "texts": cleaned_texts,
        "combined_text": combined_text,
        "image_folder": "media/",
        "image_count": len(os.listdir("media"))  # Count the number of images saved
    }

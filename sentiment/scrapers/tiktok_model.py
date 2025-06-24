import os
import re
import time
import json
import requests
import logging
from typing import List, Dict, Optional, Any
from requests import Session, Response

# Set up standard logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class TiktokCommentScraper:
    BASE_URL = 'https://www.tiktok.com'
    API_URL = BASE_URL + '/api'

    def __init__(self, timeout_minutes: int = 2):
        self.session = Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.start_time = time.time()
        self.timeout = timeout_minutes * 60
        self.media_dir = "media"
        os.makedirs(self.media_dir, exist_ok=True)

    def clean_text(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def parse_comment(self, raw: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if time.time() - self.start_time > self.timeout:
            logger.warning("Time limit reached")
            raise TimeoutError("Time limit reached")

        if not isinstance(raw, dict):
            return None

        try:
            # Replacement for jmespath - using direct dictionary access
            text = raw.get('text', '')
            image_list = raw.get('image_list', [])
            
            if not text:
                return None

            text = self.clean_text(text)
            images = []

            if isinstance(image_list, list):
                for i, img in enumerate(image_list[:3]):
                    try:
                        if not isinstance(img, dict):
                            continue
                            
                        url_list = img.get('url_list', [])
                        if not url_list:
                            continue
                            
                        url = url_list[0]
                        ext = os.path.splitext(url)[-1].split("?")[0] or ".jpg"
                        fname = f"{int(time.time() * 1000)}_{i}{ext}"
                        fpath = os.path.join(self.media_dir, fname)

                        with open(fpath, "wb") as f:
                            resp = self.session.get(url, timeout=5)
                            resp.raise_for_status()
                            f.write(resp.content)

                        images.append(fpath)
                    except Exception as e:
                        logger.warning(f"Image download failed: {e}")
                        continue

            return {
                "comment": text,
                "images": images
            }

        except Exception as e:
            logger.error(f"Error parsing comment: {e}")
            return None

    def get_comments(self, aweme_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        page = 1
        all_comments = []

        while len(all_comments) < limit:
            params = {
                'aid': 1988,
                'aweme_id': aweme_id,
                'count': 50,
                'cursor': (page - 1) * 50
            }
            try:
                resp: Response = self.session.get(f"{self.API_URL}/comment/list/", params=params)
                resp.raise_for_status()
                payload = resp.json()
            except Exception as e:
                logger.error(f"Failed to get comments: {e}")
                break

            items = payload.get("comments", [])
            if not items:
                break

            for raw in items:
                if len(all_comments) >= limit:
                    break
                try:
                    parsed = self.parse_comment(raw)
                    if parsed:
                        all_comments.append(parsed)
                except TimeoutError:
                    logger.warning("Timeout occurred while parsing comments")
                    return all_comments

            if not payload.get("has_more", False):
                break
            page += 1

        return all_comments


def scrape_tiktok_comments(aweme_input: str, limit: int = 50) -> Dict[str, List[str]]:
    match = re.search(r"/video/(\d+)", aweme_input)
    aweme_id = match.group(1) if match else aweme_input

    scraper = TiktokCommentScraper()
    comments_info = scraper.get_comments(aweme_id, limit=limit)

    comments = [item["comment"] for item in comments_info if item.get("comment")]
    images = []
    for item in comments_info:
        images.extend(item.get("images", []))

    return {
        "comments": comments,
        "images": images
    }
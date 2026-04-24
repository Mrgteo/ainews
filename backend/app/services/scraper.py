import time
import random
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from app.config import settings

logger = logging.getLogger(__name__)


class TonghuashunScraper:
    """同花顺财经电报爬虫"""

    API_URL = "https://news.10jqka.com.cn/tapp/news/push/stock/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.60",
            "Referer": "https://www.10jqka.com.cn/",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })

    def _random_delay(self, min_sec: int = None, max_sec: int = None):
        """随机延迟"""
        min_val = min_sec or settings.REQUEST_DELAY_MIN
        max_val = max_sec or settings.REQUEST_DELAY_MAX
        delay = random.uniform(min_val, max_val)
        time.sleep(delay)

    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """解析时间字符串或时间戳"""
        if not time_str:
            return None
        try:
            # 尝试时间戳（秒）
            if isinstance(time_str, (int, float)):
                return datetime.fromtimestamp(time_str)
            if str(time_str).isdigit() and len(str(time_str)) == 10:
                return datetime.fromtimestamp(int(time_str))
            if str(time_str).isdigit() and len(str(time_str)) == 13:
                return datetime.fromtimestamp(int(time_str) / 1000)

            time_str = str(time_str).strip()
            now = datetime.now()
            formats = [
                ("%Y-%m-%d %H:%M:%S", None),
                ("%Y-%m-%d %H:%M", None),
                ("%m-%d %H:%M", now.year),
                ("%H:%M", None),
            ]
            for fmt, year in formats:
                try:
                    dt = datetime.strptime(time_str, fmt)
                    if year:
                        dt = dt.replace(year=year)
                    elif dt.year == 1900:
                        dt = dt.replace(year=now.year, month=now.month, day=now.day)
                    return dt
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def _is_within_days(self, pub_time: Optional[datetime], days: int) -> bool:
        """检查发布时间是否在指定天数内"""
        if pub_time is None:
            return True
        cutoff = datetime.now() - timedelta(days=days)
        return pub_time >= cutoff

    def fetch_news_api(self, page: int = 1, page_size: int = 50) -> List[Dict[str, Any]]:
        """通过 API 获取新闻列表"""
        try:
            params = {
                "page": page,
                "tag": "",
                "track": "website",
                "pagesize": page_size
            }

            resp = self.session.get(self.API_URL, params=params, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"API 请求失败: {resp.status_code}")
                return []

            data = resp.json()
            items = data.get("data", {}).get("list", []) or data.get("list", []) or []

            news_list = []
            for item in items:
                try:
                    title = item.get("title", "")
                    url = item.get("url", "") or item.get("share_url", "")
                    source = item.get("media", "") or item.get("source", "") or "同花顺"
                    pub_time_str = item.get("ctime", "") or item.get("time", "") or item.get("pub_time", "")
                    summary = item.get("summary", "") or item.get("description", "")

                    pub_time = self._parse_time(pub_time_str)

                    if title and url:
                        news_list.append({
                            "title": title,
                            "url": url,
                            "pub_time": pub_time,
                            "source": source,
                            "summary": summary if summary else None,
                            "content": None,
                        })
                except Exception as e:
                    logger.warning(f"解析新闻项失败: {e}")
                    continue

            return news_list

        except requests.RequestException as e:
            logger.error(f"API 请求异常: {e}")
            return []
        except Exception as e:
            logger.error(f"获取新闻列表失败: {e}")
            return []

    def fetch_content_with_requests(self, url: str) -> Optional[str]:
        """使用 requests + BeautifulSoup 抓取新闻正文"""
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"请求失败 {url}: {resp.status_code}")
                return None

            soup = BeautifulSoup(resp.content, 'html.parser')

            for tag in soup.find_all(['script', 'style', 'iframe', 'ins', 'aside']):
                tag.decompose()

            content_elem = soup.select_one(".article-content, .news-content, .detail-content, #content, .main-content")
            if content_elem:
                for tag in content_elem.find_all(['script', 'style', 'iframe', 'ins', 'aside', 'div']):
                    tag.decompose()
                text = content_elem.get_text(separator='\n', strip=True)
                return text if len(text) > 50 else None

            article = soup.select_one("article")
            if article:
                text = article.get_text(separator='\n', strip=True)
                return text if len(text) > 50 else None

            paragraphs = soup.select("p")
            if paragraphs:
                texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                text = '\n'.join(texts)
                return text if len(text) > 50 else None

            body = soup.select_one("body")
            return body.get_text(separator='\n', strip=True) if body else None

        except requests.RequestException as e:
            logger.warning(f"requests 抓取失败 {url}: {e}")
            return None
        except Exception as e:
            logger.warning(f"解析内容失败 {url}: {e}")
            return None

    def scrape(self, days: int = 3) -> List[Dict[str, Any]]:
        """爬取近N天新闻"""
        all_news = []
        page = 1
        page_size = 50
        max_pages = 5

        logger.info(f"开始爬取同花顺财经，近{days}天新闻")

        while page <= max_pages:
            logger.info(f"正在爬取第 {page} 页...")
            news_list = self.fetch_news_api(page=page, page_size=page_size)

            if not news_list:
                logger.info(f"第 {page} 页无数据，停止爬取")
                break

            all_news.extend(news_list)

            has_old_news = False
            for news in news_list:
                if not self._is_within_days(news.get("pub_time"), days):
                    has_old_news = True

            if has_old_news and page >= 2:
                logger.info("已爬取到超过指定天数的新闻，停止")
                break

            page += 1
            self._random_delay(1, 2)

        filtered_news = [n for n in all_news if self._is_within_days(n.get("pub_time"), days)]
        logger.info(f"获取到 {len(all_news)} 条新闻，过滤后剩余 {len(filtered_news)} 条")

        for i, news in enumerate(filtered_news[:10]):
            url = news.get("url")
            if url:
                logger.info(f"正在抓取第 {i+1}/{min(len(filtered_news), 10)} 条新闻正文...")
                content = self.fetch_content_with_requests(url)
                if content:
                    news["content"] = content
                self._random_delay(0.5, 1.5)

        return filtered_news

    def scrape_list_only(self, days: int = 3) -> List[Dict[str, Any]]:
        """仅爬取新闻列表（不抓取正文）"""
        all_news = []
        page = 1
        page_size = 50
        max_pages = 5

        while page <= max_pages:
            news_list = self.fetch_news_api(page=page, page_size=page_size)
            if not news_list:
                break
            all_news.extend(news_list)

            has_old = any(not self._is_within_days(n.get("pub_time"), days) for n in news_list)
            if has_old and page >= 2:
                break
            page += 1
            self._random_delay(0.5, 1)

        return [n for n in all_news if self._is_within_days(n.get("pub_time"), days)]

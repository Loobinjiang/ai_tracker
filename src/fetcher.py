"""
RSS和网页内容抓取器
"""

import ssl
import certifi
import feedparser
import requests
import logging
import time
from datetime import datetime, timezone
from typing import Optional
from bs4 import BeautifulSoup
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# 使用 certifi 的证书，解决 macOS Python 的 SSL 证书问题
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


@dataclass
class Article:
    title: str
    url: str
    summary: str
    published_at: Optional[datetime]
    company: str
    region: str  # "international" | "domestic"
    source_type: str  # "rss" | "web" | "news_aggregator"
    tags: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "company": self.company,
            "region": self.region,
            "source_type": self.source_type,
            "tags": self.tags,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }


class RSSFetcher:
    """RSS订阅抓取器"""

    def __init__(self, timeout: int = 15, max_per_feed: int = 10):
        self.timeout = timeout
        self.max_per_feed = max_per_feed

    def fetch(self, url: str, company: str, region: str) -> list[Article]:
        articles = []
        try:
            logger.info(f"[RSS] 抓取 {company}: {url}")
            # 先用 requests 下载内容（使用 certifi 证书），再交给 feedparser 解析
            resp = requests.get(
                url,
                headers=HEADERS,
                timeout=self.timeout,
                verify=certifi.where(),
            )
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            feed = feedparser.parse(resp.text)

            if feed.bozo and not feed.entries:
                logger.warning(f"[RSS] 解析失败 {url}: {feed.bozo_exception}")
                return articles

            for entry in feed.entries[: self.max_per_feed]:
                published_at = self._parse_date(entry)
                summary = self._extract_summary(entry)
                article = Article(
                    title=entry.get("title", "").strip(),
                    url=entry.get("link", "").strip(),
                    summary=summary,
                    published_at=published_at,
                    company=company,
                    region=region,
                    source_type="rss",
                    tags=self._extract_tags(entry),
                )
                if article.title and article.url:
                    articles.append(article)

            logger.info(f"[RSS] {company} 获取 {len(articles)} 篇文章")
        except Exception as e:
            logger.error(f"[RSS] {company} 抓取失败: {e}")
        return articles

    def _parse_date(self, entry) -> Optional[datetime]:
        for attr in ("published_parsed", "updated_parsed", "created_parsed"):
            t = getattr(entry, attr, None)
            if t:
                try:
                    return datetime(*t[:6], tzinfo=timezone.utc)
                except Exception:
                    pass
        return None

    def _extract_summary(self, entry) -> str:
        for attr in ("summary", "description", "content"):
            raw = getattr(entry, attr, None)
            if raw:
                if isinstance(raw, list):
                    raw = raw[0].get("value", "") if raw else ""
                text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
                return text[:1500]
        return ""

    def _extract_tags(self, entry) -> list:
        tags = []
        for tag in getattr(entry, "tags", []):
            term = tag.get("term", "")
            if term:
                tags.append(term)
        return tags[:5]


class WebScraper:
    """网页内容抓取器（针对无RSS源的网站）"""

    def __init__(self, timeout: int = 20, max_articles: int = 8):
        self.timeout = timeout
        self.max_articles = max_articles
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch(self, url: str, company: str, region: str) -> list[Article]:
        articles = []
        try:
            logger.info(f"[Web] 抓取 {company}: {url}")
            resp = self.session.get(url, timeout=self.timeout, verify=certifi.where())
            resp.raise_for_status()
            # 优先使用 HTML meta charset，避免 chardet 误判中文为 windows-1252
            detected = resp.apparent_encoding or "utf-8"
            if detected.lower() in ("windows-1252", "ascii", "iso-8859-1"):
                detected = "utf-8"
            soup = BeautifulSoup(resp.content, "html.parser", from_encoding=detected)

            # 通用文章链接提取策略
            candidates = self._find_article_links(soup, url)
            for title, link, summary in candidates[: self.max_articles]:
                articles.append(
                    Article(
                        title=title,
                        url=link,
                        summary=summary,
                        published_at=None,
                        company=company,
                        region=region,
                        source_type="web",
                    )
                )
            logger.info(f"[Web] {company} 获取 {len(articles)} 篇文章")
        except Exception as e:
            logger.error(f"[Web] {company} 抓取失败: {e}")
        return articles

    def _find_article_links(self, soup: BeautifulSoup, base_url: str) -> list[tuple]:
        results = []
        seen_urls = set()

        # 优先查找文章容器
        article_selectors = [
            "article", ".post", ".blog-post", ".news-item",
            ".entry", ".card", "[class*='article']", "[class*='post']",
            "[class*='news']", "[class*='blog']",
        ]

        containers = []
        for sel in article_selectors:
            containers.extend(soup.select(sel))

        if not containers:
            # 降级：找所有有标题的链接
            containers = soup.find_all(["li", "div"], limit=50)

        for container in containers[:30]:
            link_tag = container.find("a", href=True)
            heading = container.find(["h1", "h2", "h3", "h4"])

            if not link_tag:
                continue

            href = link_tag["href"]
            if not href.startswith("http"):
                from urllib.parse import urljoin
                href = urljoin(base_url, href)

            if href in seen_urls or "#" in href:
                continue
            seen_urls.add(href)

            title = (heading or link_tag).get_text(strip=True)
            if len(title) < 5 or len(title) > 300:
                continue

            # 简短摘要
            p = container.find("p")
            summary = p.get_text(strip=True)[:1000] if p else ""

            results.append((title, href, summary))

        return results


class NewsFetcher:
    """新闻聚合RSS抓取器"""

    AI_KEYWORDS = {
        "en": [
            "AI", "artificial intelligence", "machine learning", "deep learning",
            "LLM", "language model", "GPT", "Claude", "Gemini", "chatbot",
            "neural network", "generative AI", "foundation model", "multimodal",
        ],
        "zh": [
            "人工智能", "AI", "大模型", "语言模型", "机器学习", "深度学习",
            "生成式", "多模态", "智能体", "神经网络", "大语言", "GPT", "Claude",
        ],
    }

    def __init__(self, rss_fetcher: RSSFetcher):
        self.rss_fetcher = rss_fetcher

    def fetch(self, name: str, rss_url: str, category: str) -> list[Article]:
        all_articles = self.rss_fetcher.fetch(rss_url, name, "aggregator")
        # 过滤AI相关文章
        filtered = []
        for art in all_articles:
            if self._is_ai_related(art.title + " " + art.summary):
                art.source_type = "news_aggregator"
                art.tags.append(category)
                filtered.append(art)
        logger.info(f"[News] {name} AI相关文章: {len(filtered)}/{len(all_articles)}")
        return filtered

    def _is_ai_related(self, text: str) -> bool:
        text_lower = text.lower()
        all_keywords = self.AI_KEYWORDS["en"] + self.AI_KEYWORDS["zh"]
        return any(kw.lower() in text_lower for kw in all_keywords)


class InvestFetcher:
    """
    投资内容抓取器
    - 雪球：段永平（大道无形我有型）
    - 微信公众号：辉哥奇谭（通过 RSS 桥接服务）
    """

    # 段永平雪球用户ID
    DYP_URL = "https://xueqiu.com/u/8152922776"
    DYP_RSS = "https://rsshub.app/xueqiu/user/8152922776"

    # 辉哥奇谭微信公众号 RSS（通过多种桥接尝试）
    HGG_RSS_CANDIDATES = [
        "https://rsshub.app/wechat/huigeqitan",
        "https://rss.shab.fun/wechat/huigeqitan",
        "https://feeds.feedburner.com/huigeqitan",
    ]
    HGG_WECHAT_ID = "huigeqitan"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch_dyp(self) -> list[dict]:
        """抓取段永平雪球最新发布"""
        items = []

        # 方案1：尝试 RSSHub
        try:
            resp = self.session.get(self.DYP_RSS, timeout=self.timeout, verify=certifi.where())
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            if feed.entries:
                for entry in feed.entries[:5]:
                    title = entry.get("title", "").strip()
                    url = entry.get("link", "").strip()
                    summary = BeautifulSoup(
                        entry.get("summary", ""), "html.parser"
                    ).get_text(" ", strip=True)[:500]
                    if url:
                        items.append({
                            "source": "段永平",
                            "title": title or summary[:50],
                            "url": url,
                            "content": summary,
                            "published_at": None,
                        })
                logger.info(f"[投资] 段永平 via RSSHub 获取 {len(items)} 条")
                return items
        except Exception as e:
            logger.warning(f"[投资] 段永平 RSSHub 失败: {e}")

        # 方案2：直接抓取雪球页面
        try:
            url = self.DYP_URL
            resp = self.session.get(url, timeout=self.timeout, verify=certifi.where())
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")
            posts = soup.select(".timeline-item, .status-item, [class*='post']")[:5]
            for post in posts:
                text_el = post.find(["p", "div", "span"])
                text = text_el.get_text(strip=True)[:300] if text_el else ""
                link_el = post.find("a", href=True)
                link = link_el["href"] if link_el else url
                if not link.startswith("http"):
                    link = "https://xueqiu.com" + link
                if text:
                    items.append({
                        "source": "段永平",
                        "title": text[:50] + "...",
                        "url": link,
                        "content": text,
                        "published_at": None,
                    })
            logger.info(f"[投资] 段永平 直抓 获取 {len(items)} 条")
        except Exception as e:
            logger.warning(f"[投资] 段永平 直抓失败: {e}")

        return items

    def fetch_huige(self) -> list[dict]:
        """抓取辉哥奇谭最新文章"""
        items = []

        # 尝试多个 RSS 桥接源
        for rss_url in self.HGG_RSS_CANDIDATES:
            try:
                resp = self.session.get(rss_url, timeout=self.timeout, verify=certifi.where())
                resp.raise_for_status()
                feed = feedparser.parse(resp.text)
                if feed.entries:
                    for entry in feed.entries[:3]:
                        title = entry.get("title", "").strip()
                        url = entry.get("link", "").strip()
                        summary = BeautifulSoup(
                            entry.get("summary", ""), "html.parser"
                        ).get_text(" ", strip=True)[:600]
                        if url:
                            items.append({
                                "source": "辉哥奇谭",
                                "title": title,
                                "url": url,
                                "content": summary,
                                "published_at": None,
                            })
                    logger.info(f"[投资] 辉哥奇谭 via {rss_url} 获取 {len(items)} 条")
                    return items
            except Exception as e:
                logger.warning(f"[投资] 辉哥奇谭 {rss_url} 失败: {e}")

        # 兜底：返回固定入口链接供手动查看
        logger.warning("[投资] 辉哥奇谭 所有RSS源失败，返回公众号入口")
        items.append({
            "source": "辉哥奇谭",
            "title": "辉哥奇谭（点击查看最新文章）",
            "url": "https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=MzI5OTM4MjYwNA==",
            "content": "微信公众号 RSS 暂时不可用，请手动访问查看最新内容。",
            "published_at": None,
        })
        return items

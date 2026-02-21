"""
数据存储与去重模块（使用SQLite）
"""

import sqlite3
import json
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from .fetcher import Article

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "articles.db"


class Storage:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id          TEXT PRIMARY KEY,
                    title       TEXT NOT NULL,
                    url         TEXT NOT NULL UNIQUE,
                    summary     TEXT,
                    published_at TEXT,
                    company     TEXT,
                    region      TEXT,
                    source_type TEXT,
                    tags        TEXT,
                    fetched_at  TEXT,
                    is_read     INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_company ON articles(company)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_published_at ON articles(published_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_region ON articles(region)
            """)
            # 投资内容表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invest_items (
                    id          TEXT PRIMARY KEY,
                    source      TEXT NOT NULL,
                    title       TEXT,
                    url         TEXT NOT NULL UNIQUE,
                    content     TEXT,
                    published_at TEXT,
                    fetched_at  TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_invest_source ON invest_items(source)
            """)
            conn.commit()

    @staticmethod
    def _make_id(url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def save(self, article: Article) -> bool:
        """保存文章，返回是否为新文章（去重）"""
        article_id = self._make_id(article.url)
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO articles
                    (id, title, url, summary, published_at, company, region,
                     source_type, tags, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        article_id,
                        article.title,
                        article.url,
                        article.summary,
                        article.published_at.isoformat() if article.published_at else None,
                        article.company,
                        article.region,
                        article.source_type,
                        json.dumps(article.tags, ensure_ascii=False),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                return conn.execute("SELECT changes()").fetchone()[0] > 0
        except Exception as e:
            logger.error(f"保存文章失败 [{article.title}]: {e}")
            return False

    def save_many(self, articles: list[Article]) -> tuple[int, int]:
        """批量保存，返回 (新增数, 重复数)"""
        if not articles:
            return 0, 0
        now = datetime.now(timezone.utc).isoformat()
        rows = [
            (
                self._make_id(art.url),
                art.title,
                art.url,
                art.summary,
                art.published_at.isoformat() if art.published_at else None,
                art.company,
                art.region,
                art.source_type,
                json.dumps(art.tags, ensure_ascii=False),
                now,
            )
            for art in articles
        ]
        try:
            with self._get_conn() as conn:
                conn.executemany(
                    """
                    INSERT OR IGNORE INTO articles
                    (id, title, url, summary, published_at, company, region,
                     source_type, tags, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )
                new_count = conn.execute("SELECT changes()").fetchone()[0]
        except Exception as e:
            logger.error(f"批量保存文章失败: {e}")
            return 0, len(articles)
        return new_count, len(articles) - new_count

    def get_recent(
        self,
        days: int = 7,
        company: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """获取最近N天的文章"""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        conditions = ["fetched_at >= ?"]
        params: list = [since]

        if company:
            conditions.append("company = ?")
            params.append(company)
        if region:
            conditions.append("region = ?")
            params.append(region)

        where = " AND ".join(conditions)
        with self._get_conn() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM articles
                WHERE {where}
                ORDER BY COALESCE(published_at, fetched_at) DESC
                LIMIT ?
                """,
                params + [limit],
            ).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        """获取数据库统计信息"""
        with self._get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
            by_company = conn.execute(
                """
                SELECT company, COUNT(*) as cnt
                FROM articles
                GROUP BY company
                ORDER BY cnt DESC
                """
            ).fetchall()
            by_region = conn.execute(
                """
                SELECT region, COUNT(*) as cnt
                FROM articles
                GROUP BY region
                """
            ).fetchall()
        return {
            "total": total,
            "by_company": {r["company"]: r["cnt"] for r in by_company},
            "by_region": {r["region"]: r["cnt"] for r in by_region},
        }

    def is_url_exists(self, url: str) -> bool:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM articles WHERE url = ?", (url,)
            ).fetchone()
        return row is not None

    def save_invest_item(self, source: str, title: str, url: str, content: str, published_at: str = None) -> bool:
        """保存投资内容，返回是否为新条目"""
        item_id = hashlib.sha256(url.encode()).hexdigest()[:16]
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO invest_items
                    (id, source, title, url, content, published_at, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_id, source, title, url, content,
                        published_at,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                return conn.execute("SELECT changes()").fetchone()[0] > 0
        except Exception as e:
            logger.error(f"保存投资内容失败 [{title}]: {e}")
            return False

    def get_invest_recent(self, days: int = 7) -> list[dict]:
        """获取最近N天的投资内容"""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM invest_items
                WHERE fetched_at >= ?
                ORDER BY COALESCE(published_at, fetched_at) DESC
                """,
                (since,),
            ).fetchall()
        return [dict(r) for r in rows]

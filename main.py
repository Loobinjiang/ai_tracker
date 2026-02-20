#!/usr/bin/env python3
"""
AI公司最新进展自动抓取工具
用法:
  python main.py             # 抓取并生成日报
  python main.py --weekly    # 生成周报
  python main.py --report-only  # 仅生成报告（不抓取）
  python main.py --schedule  # 启动定时任务（每6小时抓取一次）
  python main.py --company "OpenAI"  # 只抓取指定公司
  python main.py --stats     # 显示数据库统计
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# 确保项目根目录在路径中
sys.path.insert(0, str(Path(__file__).parent))

from src.fetcher import RSSFetcher, WebScraper, NewsFetcher, InvestFetcher
from src.storage import Storage
from src.reporter import Reporter
from src.sources import AI_SOURCES, NEWS_AGGREGATORS

# 日志配置
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "tracker.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")


def crawl(
    storage: Storage,
    target_company: str | None = None,
    include_aggregators: bool = True,
) -> list:
    """执行抓取任务"""
    rss_fetcher = RSSFetcher(timeout=15, max_per_feed=10)
    web_scraper = WebScraper(timeout=20, max_articles=8)
    news_fetcher = NewsFetcher(rss_fetcher)

    all_new_articles = []
    total_new = 0
    total_dup = 0

    sources = AI_SOURCES
    if target_company:
        sources = {k: v for k, v in AI_SOURCES.items() if k == target_company}
        if not sources:
            logger.warning(f"未找到公司: {target_company}")
            print(f"可用公司列表: {', '.join(AI_SOURCES.keys())}")
            return []

    logger.info(f"开始抓取 {len(sources)} 个AI公司信息源...")

    for company, config in sources.items():
        region = config.get("region", "unknown")
        company_articles = []

        # RSS抓取
        for rss_url in config.get("rss_feeds", []):
            articles = rss_fetcher.fetch(rss_url, company, region)
            company_articles.extend(articles)
            time.sleep(0.5)

        # 网页抓取（无RSS源的公司）
        if config.get("web_scrape") and not config.get("rss_feeds"):
            blog_url = config.get("blog_url") or config.get("news_url", "")
            if blog_url:
                articles = web_scraper.fetch(blog_url, company, region)
                company_articles.extend(articles)
                time.sleep(1)

        new, dup = storage.save_many(company_articles)
        total_new += new
        total_dup += dup
        all_new_articles.extend(
            [a for a in company_articles if storage.is_url_exists(a.url)]
        )
        if company_articles:
            logger.info(f"  {company}: +{new} 新增, {dup} 重复")

    # 新闻聚合源
    if include_aggregators and not target_company:
        logger.info(f"抓取 {len(NEWS_AGGREGATORS)} 个新闻聚合源...")
        for name, config in NEWS_AGGREGATORS.items():
            articles = news_fetcher.fetch(name, config["rss"], config["category"])
            new, dup = storage.save_many(articles)
            total_new += new
            total_dup += dup
            time.sleep(0.5)

    logger.info(f"\n抓取完成 — 新增: {total_new} | 重复跳过: {total_dup}")
    return all_new_articles


def crawl_invest(storage: Storage) -> int:
    """抓取投资内容（段永平雪球 + 辉哥奇谭）"""
    fetcher = InvestFetcher(timeout=15)
    total_new = 0

    logger.info("抓取投资内容...")

    # 段永平
    dyp_items = fetcher.fetch_dyp()
    for item in dyp_items:
        is_new = storage.save_invest_item(
            source=item["source"],
            title=item["title"],
            url=item["url"],
            content=item["content"],
            published_at=item.get("published_at"),
        )
        if is_new:
            total_new += 1

    # 辉哥奇谭
    hgg_items = fetcher.fetch_huige()
    for item in hgg_items:
        is_new = storage.save_invest_item(
            source=item["source"],
            title=item["title"],
            url=item["url"],
            content=item["content"],
            published_at=item.get("published_at"),
        )
        if is_new:
            total_new += 1

    logger.info(f"投资内容抓取完成 — 新增: {total_new} 条")
    return total_new


def run_schedule(interval_hours: int = 6):
    """定时运行"""
    logger.info(f"定时模式启动，每 {interval_hours} 小时抓取一次（Ctrl+C 退出）")
    storage = Storage()
    reporter = Reporter(storage)
    while True:
        logger.info("=== 开始定时抓取 ===")
        crawl(storage)
        reporter.generate_daily_report(days=1)
        logger.info(f"下次抓取将在 {interval_hours} 小时后...")
        time.sleep(interval_hours * 3600)


def main():
    parser = argparse.ArgumentParser(
        description="AI公司最新进展自动抓取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--weekly", action="store_true", help="生成周报")
    parser.add_argument("--report-only", action="store_true", help="仅生成报告，不抓取")
    parser.add_argument("--schedule", action="store_true", help="启动定时任务")
    parser.add_argument("--company", type=str, help="只抓取指定公司")
    parser.add_argument("--stats", action="store_true", help="显示数据库统计")
    parser.add_argument("--days", type=int, default=1, help="报告覆盖天数（默认1天）")
    parser.add_argument("--interval", type=int, default=6, help="定时间隔（小时，默认6）")
    parser.add_argument("--no-aggregators", action="store_true", help="不抓取新闻聚合源")
    args = parser.parse_args()

    storage = Storage()
    reporter = Reporter(storage)

    # 定时模式
    if args.schedule:
        run_schedule(interval_hours=args.interval)
        return

    # 统计模式
    if args.stats:
        stats = storage.get_stats()
        print(f"\n数据库统计:")
        print(f"  总文章数: {stats['total']}")
        print(f"\n  按地区:")
        for region, cnt in stats["by_region"].items():
            print(f"    {region}: {cnt}")
        print(f"\n  各公司文章数（Top 20）:")
        for company, cnt in list(stats["by_company"].items())[:20]:
            print(f"    {company}: {cnt}")
        return

    # 抓取
    if not args.report_only:
        crawl(
            storage,
            target_company=args.company,
            include_aggregators=not args.no_aggregators,
        )
        # 抓取投资内容
        if not args.company:
            crawl_invest(storage)

    # 生成报告
    if args.weekly:
        report_path = reporter.generate_weekly_report()
    else:
        report_path = reporter.generate_daily_report(days=args.days)

    # 终端摘要
    days = 7 if args.weekly else args.days
    articles = storage.get_recent(days=days, limit=100)
    reporter.print_summary(articles)
    print(f"完整报告已保存至: {report_path}\n")


if __name__ == "__main__":
    main()

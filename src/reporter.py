"""
报告生成模块：生成精简日报格式
输出格式：
  【AI全球进展 · 国际】
  - 一句话动态（含链接）

  【AI全球进展 · 国内】
  - 一句话动态（含链接）

  【段永平 雪球最新】
  - 观点1
  - 观点2

  【辉哥奇谭 最新】
  标题：xxx
  核心：xxx
"""

import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

from .storage import Storage

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "reports"

# 重点关注的国际公司（过滤用）
INTL_KEY_COMPANIES = {
    "OpenAI", "Anthropic", "Google DeepMind", "Google AI",
    "Meta AI", "Microsoft Research", "xAI", "Mistral AI",
    "Hugging Face", "Perplexity AI",
}

# 重点关注的国内公司（过滤用）
DOM_KEY_COMPANIES = {
    "字节跳动AI", "百度AI", "阿里云通义", "腾讯AI",
    "华为昇腾", "智谱AI", "月之暗面", "MiniMax",
    "深度求索", "零一万物",
}

# 国内聚合媒体（补充国内AI动态）
DOMESTIC_AGGREGATORS = {"机器之心", "量子位"}


class Reporter:
    def __init__(self, storage: Storage):
        self.storage = storage
        REPORTS_DIR.mkdir(exist_ok=True)

    def generate_daily_report(self, days: int = 1) -> Path:
        """生成日报"""
        articles = self.storage.get_recent(days=days, limit=300)
        invest_items = self.storage.get_invest_recent(days=days)
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = REPORTS_DIR / f"ai_report_{date_str}.md"
        content = self._build_markdown(articles, invest_items, date_str, days)
        filename.write_text(content, encoding="utf-8")
        logger.info(f"报告已生成: {filename}")
        return filename

    def generate_weekly_report(self) -> Path:
        """生成周报"""
        articles = self.storage.get_recent(days=7, limit=500)
        invest_items = self.storage.get_invest_recent(days=7)
        week_str = datetime.now().strftime("%Y-W%W")
        filename = REPORTS_DIR / f"ai_report_{week_str}.md"
        content = self._build_markdown(articles, invest_items, week_str, 7)
        filename.write_text(content, encoding="utf-8")
        logger.info(f"周报已生成: {filename}")
        return filename

    def _build_markdown(self, articles: list[dict], invest_items: list[dict], date_str: str, days: int) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"# AI & 投资日报 · {date_str}",
            f"\n> 生成时间: {now} | 覆盖周期: 近{days}天\n",
            "---\n",
        ]

        if not articles and not invest_items:
            lines.append("_暂无最新资讯，请稍后重新运行抓取。_")
            return "\n".join(lines)

        # ---- 【AI全球进展 · 国际】 ----
        intl_articles = self._get_intl_articles(articles)
        lines.append("## 【AI全球进展 · 国际】\n")
        if intl_articles:
            for art in intl_articles:
                lines.append(self._format_oneliner(art))
        else:
            lines.append("_暂无国际动态_")
        lines.append("")

        # ---- 【AI全球进展 · 国内】 ----
        dom_articles = self._get_dom_articles(articles)
        lines.append("---\n")
        lines.append("## 【AI全球进展 · 国内】\n")
        if dom_articles:
            for art in dom_articles:
                lines.append(self._format_oneliner(art))
        else:
            lines.append("_暂无国内动态_")
        lines.append("")

        # ---- 【段永平 雪球最新】 ----
        dyp_items = [i for i in invest_items if i.get("source") == "段永平"]
        lines.append("---\n")
        lines.append("## 【段永平 雪球最新】\n")
        if dyp_items:
            for item in dyp_items[:5]:
                title = item.get("title", "").strip()
                content = item.get("content", "").strip()
                url = item.get("url", "")
                if title:
                    lines.append(f"- **[{title}]({url})**")
                if content:
                    for point in content.split("\n"):
                        point = point.strip()
                        if point:
                            lines.append(f"  - {point}")
        else:
            lines.append("_暂无最新内容（雪球访问受限，请手动查看）_")
        lines.append("")

        # ---- 【辉哥奇谭 最新】 ----
        hgg_items = [i for i in invest_items if i.get("source") == "辉哥奇谭"]
        lines.append("---\n")
        lines.append("## 【辉哥奇谭 最新】\n")
        if hgg_items:
            for item in hgg_items[:3]:
                title = item.get("title", "").strip()
                summary = item.get("content", "").strip()
                url = item.get("url", "")
                lines.append(f"**标题：[{title}]({url})**\n")
                if summary:
                    lines.append(f"核心：{summary}\n")
        else:
            lines.append("_暂无最新内容（微信公众号访问受限，请手动查看）_")
        lines.append("")

        lines += [
            "---",
            f"\n_由 AI Tracker 自动生成 · {now}_",
        ]
        return "\n".join(lines)

    def _get_intl_articles(self, articles: list[dict]) -> list[dict]:
        """获取国际AI动态：优先来自官方源，次选聚合媒体报道国际公司的"""
        result = []
        seen_titles = set()

        # 1. 官方来源
        for art in articles:
            company = art.get("company", "")
            if (art.get("region") == "international"
                    and art.get("source_type") != "news_aggregator"
                    and company in INTL_KEY_COMPANIES):
                t = art.get("title", "")
                if t not in seen_titles:
                    seen_titles.add(t)
                    result.append(art)

        # 2. 聚合媒体补充国际动态
        for art in articles:
            if art.get("source_type") == "news_aggregator":
                company = art.get("company", "")
                if company not in DOMESTIC_AGGREGATORS:
                    t = art.get("title", "")
                    if t not in seen_titles:
                        seen_titles.add(t)
                        result.append(art)

        return result

    def _get_dom_articles(self, articles: list[dict]) -> list[dict]:
        """获取国内AI动态：官方源 + 国内聚合媒体"""
        result = []
        seen_titles = set()

        # 1. 官方来源
        for art in articles:
            company = art.get("company", "")
            if (art.get("region") == "domestic"
                    and company in DOM_KEY_COMPANIES):
                t = art.get("title", "")
                if t not in seen_titles:
                    seen_titles.add(t)
                    result.append(art)

        # 2. 国内聚合媒体（机器之心、量子位）
        for art in articles:
            if (art.get("source_type") == "news_aggregator"
                    and art.get("company") in DOMESTIC_AGGREGATORS):
                t = art.get("title", "")
                if t not in seen_titles:
                    seen_titles.add(t)
                    result.append(art)

        return result

    def _format_oneliner(self, art: dict) -> str:
        """格式化为一行：- 公司 · 标题（链接）+ 一句摘要"""
        title = art.get("title", "无标题").strip()
        url = art.get("url", "#")
        company = art.get("company", "")
        summary = art.get("summary", "").strip()

        # 取摘要首句（到第一个句号/换行为止）
        first_sentence = ""
        if summary:
            for sep in ["。", ". ", "\n", "…"]:
                idx = summary.find(sep)
                if 0 < idx < 120:
                    first_sentence = summary[:idx + 1].strip()
                    break
            if not first_sentence:
                first_sentence = summary[:100].strip()

        line = f"- **{company}** · [{title}]({url})"
        if first_sentence:
            line += f"\n  > {first_sentence}"
        return line

    def print_summary(self, articles: list[dict]):
        """在终端打印简洁摘要"""
        if not articles:
            print("暂无最新资讯。")
            return

        by_region = defaultdict(list)
        for a in articles:
            by_region[a.get("region", "unknown")].append(a)

        print(f"\n{'='*60}")
        print(f"  AI公司最新进展 — 共 {len(articles)} 条")
        print(f"{'='*60}")

        for region_name, region_key in [("国际", "international"), ("国内", "domestic"), ("聚合", "aggregator")]:
            region_arts = by_region.get(region_key, [])
            if region_key == "aggregator":
                region_arts = [a for a in articles if a.get("source_type") == "news_aggregator"]
            if not region_arts:
                continue
            print(f"\n[{region_name}] ({len(region_arts)} 条)")
            by_company = defaultdict(list)
            for a in region_arts:
                by_company[a.get("company", "未知")].append(a)
            for company, arts in sorted(by_company.items()):
                print(f"  {company} ({len(arts)}篇):")
                for art in arts[:3]:
                    t = art.get("title", "")[:70]
                    print(f"    • {t}")
                if len(arts) > 3:
                    print(f"    ... 还有 {len(arts)-3} 篇")

        print(f"\n{'='*60}\n")

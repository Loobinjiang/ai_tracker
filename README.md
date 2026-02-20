# AI公司最新进展自动抓取工具

自动抓取国内外主要AI公司的官方博客、RSS订阅和新闻资讯，生成结构化报告。

## 覆盖范围

**国际AI公司（11家）**
- OpenAI、Anthropic、Google DeepMind、Google AI
- Meta AI、Microsoft Research、Mistral AI
- Hugging Face、Stability AI、Cohere、xAI (Grok)、Perplexity

**国内AI公司（11家）**
- 百度AI、阿里云通义千问、腾讯AI Lab
- 字节跳动、华为昇腾、智谱AI、月之暗面(Kimi)
- MiniMax、零一万物、深度求索(DeepSeek)

**新闻聚合源（6个）**
- MIT Tech Review、VentureBeat AI、The Verge AI
- InfoQ AI、机器之心、量子位

## 安装

```bash
cd ai_tracker

# 方式1：pip安装
pip install -r requirements.txt

# 方式2：使用uv（推荐）
uv pip install -r requirements.txt
```

## 使用方法

```bash
# 抓取并生成今日日报
python main.py

# 生成周报（过去7天）
python main.py --weekly

# 仅基于已有数据生成报告（不发起网络请求）
python main.py --report-only

# 只抓取指定公司
python main.py --company "OpenAI"
python main.py --company "深度求索"

# 显示数据库统计
python main.py --stats

# 启动定时抓取（每6小时一次，持续运行）
python main.py --schedule

# 自定义定时间隔（每2小时）
python main.py --schedule --interval 2

# 不包含新闻聚合源
python main.py --no-aggregators
```

## 定时任务（crontab）

```bash
# 编辑crontab
crontab -e

# 每6小时运行一次
0 */6 * * * /path/to/ai_tracker/scheduler.sh >> /path/to/ai_tracker/logs/cron.log 2>&1

# 每天早上8点运行
0 8 * * * /path/to/ai_tracker/scheduler.sh
```

## 项目结构

```
ai_tracker/
├── main.py              # 主入口
├── requirements.txt     # Python依赖
├── scheduler.sh         # cron调度脚本
├── src/
│   ├── sources.py       # AI公司信息源配置
│   ├── fetcher.py       # RSS/网页抓取器
│   ├── storage.py       # SQLite数据存储与去重
│   └── reporter.py      # Markdown报告生成
├── data/
│   └── articles.db      # SQLite数据库（自动创建）
├── reports/             # 生成的Markdown报告
└── logs/                # 运行日志
```

## 输出示例

报告保存在 `reports/` 目录下，格式为 `ai_report_YYYY-MM-DD.md`，包含：

- 国际AI公司动态（按公司分组）
- 国内AI公司动态（按公司分组）
- 综合资讯（来自新闻聚合源，已过滤AI相关内容）
- 统计摘要

## 扩展：添加新数据源

编辑 `src/sources.py`：

```python
AI_SOURCES["新公司名"] = {
    "region": "domestic",          # 或 "international"
    "rss_feeds": ["https://..."],  # RSS链接（优先）
    "blog_url": "https://...",     # 无RSS时用网页抓取
    "description": "说明",
    "web_scrape": True,            # 启用网页抓取
}
```

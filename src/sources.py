"""
AI公司信息源配置
涵盖国内外主要AI公司的官方博客、RSS订阅
"""

AI_SOURCES = {
    # ===== 国际AI公司 =====
    "OpenAI": {
        "region": "international",
        "rss_feeds": [
            "https://openai.com/blog/rss.xml",
        ],
        "blog_url": "https://openai.com/blog",
        "description": "OpenAI官方博客",
    },
    "Anthropic": {
        "region": "international",
        "rss_feeds": [],
        "blog_url": "https://www.anthropic.com/news",
        "description": "Anthropic官方新闻",
        "web_scrape": True,
    },
    "Google DeepMind": {
        "region": "international",
        "rss_feeds": [
            "https://deepmind.google/blog/rss.xml",
        ],
        "blog_url": "https://deepmind.google/blog",
        "description": "Google DeepMind博客",
    },
    "Google AI": {
        "region": "international",
        "rss_feeds": [
            "https://blog.google/technology/ai/rss/",
        ],
        "blog_url": "https://blog.google/technology/ai/",
        "description": "Google AI博客",
    },
    "Meta AI": {
        "region": "international",
        "rss_feeds": [],
        "blog_url": "https://ai.meta.com/blog",
        "description": "Meta AI博客",
        "web_scrape": True,
    },
    "Microsoft Research": {
        "region": "international",
        "rss_feeds": [
            "https://www.microsoft.com/en-us/research/feed/",
        ],
        "blog_url": "https://www.microsoft.com/en-us/research/blog",
        "description": "微软研究院博客",
    },
    "Mistral AI": {
        "region": "international",
        "rss_feeds": [],
        "blog_url": "https://mistral.ai/news",
        "description": "Mistral AI新闻",
        "web_scrape": True,
    },
    "Hugging Face": {
        "region": "international",
        "rss_feeds": [
            "https://huggingface.co/blog/feed.xml",
        ],
        "blog_url": "https://huggingface.co/blog",
        "description": "Hugging Face博客",
    },
    "Stability AI": {
        "region": "international",
        "rss_feeds": [],
        "blog_url": "https://stability.ai/blog",
        "description": "Stability AI博客",
        "web_scrape": True,
    },
    "Cohere": {
        "region": "international",
        "rss_feeds": [
            "https://cohere.com/blog/rss",
        ],
        "blog_url": "https://cohere.com/blog",
        "description": "Cohere博客",
    },
    "xAI": {
        "region": "international",
        "rss_feeds": [],
        "blog_url": "https://x.ai/blog",
        "description": "xAI (Grok) 博客",
        "web_scrape": True,
    },
    "Perplexity AI": {
        "region": "international",
        "rss_feeds": [],
        "blog_url": "https://blog.perplexity.ai",
        "description": "Perplexity AI博客",
        "web_scrape": True,
    },

    # ===== 国内AI公司 =====
    "百度AI": {
        "region": "domestic",
        "rss_feeds": [],
        "blog_url": "https://ai.baidu.com/forum",
        "news_url": "https://home.baidu.com/home/index/news",
        "description": "百度AI官方动态",
        "web_scrape": True,
    },
    "阿里云通义": {
        "region": "domestic",
        "rss_feeds": [],
        "blog_url": "https://tongyi.aliyun.com",
        "description": "阿里云通义千问",
        "web_scrape": True,
    },
    "腾讯AI": {
        "region": "domestic",
        "rss_feeds": [],
        "blog_url": "https://ai.tencent.com/ailab/zh/news",
        "description": "腾讯AI Lab",
        "web_scrape": True,
    },
    "字节跳动AI": {
        "region": "domestic",
        "rss_feeds": [],
        "blog_url": "https://www.bytedance.com/zh/news",
        "description": "字节跳动AI动态",
        "web_scrape": True,
    },
    "华为昇腾": {
        "region": "domestic",
        "rss_feeds": [],
        "blog_url": "https://www.huawei.com/cn/news",
        "description": "华为AI动态",
        "web_scrape": True,
    },
    "智谱AI": {
        "region": "domestic",
        "rss_feeds": [],
        "blog_url": "https://www.zhipuai.cn/news",
        "description": "智谱AI新闻",
        "web_scrape": True,
    },
    "月之暗面": {
        "region": "domestic",
        "rss_feeds": [],
        "blog_url": "https://www.moonshot.cn",
        "description": "月之暗面(Kimi)",
        "web_scrape": True,
    },
    "MiniMax": {
        "region": "domestic",
        "rss_feeds": [],
        "blog_url": "https://www.minimaxi.com/news",
        "description": "MiniMax AI",
        "web_scrape": True,
    },
    "零一万物": {
        "region": "domestic",
        "rss_feeds": [],
        "blog_url": "https://www.lingyiwanwu.com/news",
        "description": "零一万物",
        "web_scrape": True,
    },
    "深度求索": {
        "region": "domestic",
        "rss_feeds": [],
        "blog_url": "https://www.deepseek.com",
        "description": "DeepSeek (深度求索)",
        "web_scrape": True,
    },
    "步步高天鹅绒": {
        "region": "domestic",
        "rss_feeds": [],
        "blog_url": "https://www.vivo.com.cn/ai",
        "description": "vivo天鹅绒AI",
        "web_scrape": True,
    },
}

# 新闻聚合源（综合报道AI公司进展）
NEWS_AGGREGATORS = {
    "MIT Tech Review AI": {
        "rss": "https://www.technologyreview.com/feed/",
        "category": "AI",
    },
    "VentureBeat AI": {
        "rss": "https://venturebeat.com/category/ai/feed/",
        "category": "AI",
    },
    "The Verge AI": {
        "rss": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "category": "AI",
    },
    "InfoQ AI": {
        "rss": "https://feed.infoq.com/",
        "category": "AI",
    },
    "机器之心": {
        "rss": "https://www.jiqizhixin.com/rss",
        "category": "AI国内资讯",
    },
    "量子位": {
        "rss": "https://www.qbitai.com/rss",
        "category": "AI国内资讯",
    },
}

"""Summarize articles using Google Gemini (free tier)."""

import time
import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_MODEL


def _get_prompt(article: dict) -> str:
    return f"""用中文回答。

你是一个专业的房地产市场分析师，专注于美国麻萨诸塞州(Massachusetts)的房地产市场。请对以下新闻进行分析：

**标题**: {article['title']}
**来源**: {article['source']}
**摘要**: {article['summary']}

请严格按照以下格式输出（必须包含【标题】【总结】和【分析】三个标记）：

【标题】
（将原标题翻译为简洁的中文标题，保留关键地名和数据）

【总结】
（3-5句话，完整概括新闻核心内容，包括涉及的地区、政策、数据、项目等）

【分析】
（1-2句话，从房地产开发商/投资者的角度，这条新闻对麻州房地产市场有什么影响？对哪些地区/物业类型可能有影响？对买地开发卖出的业务模式有何启示？）

要求：语言简洁专业，保留具体数字/数据。必须同时输出【标题】【总结】和【分析】三部分。"""


def summarize_articles(articles: list[dict]) -> list[dict]:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    results = []
    for i, article in enumerate(articles):
        try:
            response = model.generate_content(_get_prompt(article))
            text = response.text
            if '【标题】' in text and '【总结】' in text:
                cn_title = text.split('【总结】')[0].split('【标题】')[1].strip()
                if cn_title:
                    article["title_cn"] = cn_title
                text = '【总结】' + text.split('【总结】', 1)[1]
            article["ai_summary"] = text
        except Exception as e:
            article["ai_summary"] = f"(总结生成失败: {e})"

        results.append(article)

        if i < len(articles) - 1:
            time.sleep(4.5)

    return results

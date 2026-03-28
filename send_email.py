"""Render HTML email and send via Gmail SMTP."""

import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import SMTP_SERVER, SMTP_PORT, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT


def render_email(articles: list[dict], market_data: str = "") -> str:
    template_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("email_template.html")

    now = datetime.now(timezone.utc)
    html = template.render(
        date=now.strftime("%Y年%m月%d日"),
        article_count=len(articles),
        articles=articles,
        market_data=market_data,
    )
    return html


def send_email(html: str, article_count: int):
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT]):
        raise ValueError("Email credentials not configured.")

    now = datetime.now(timezone.utc)
    subject = f"🏠 麻州房产日报 - {now.strftime('%Y/%m/%d')} ({article_count}篇)"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"MA Real Estate Digest <{EMAIL_SENDER}>"
    msg["To"] = EMAIL_RECIPIENT

    plain = f"麻州房产日报已生成，共 {article_count} 篇新闻。请使用 HTML 邮件客户端查看。"
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, [EMAIL_RECIPIENT], msg.as_string())

    print(f"Email sent to {EMAIL_RECIPIENT}")

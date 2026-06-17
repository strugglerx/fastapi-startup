"""极简 SMTP 发件器
- 用 stdlib smtplib，不引入第三方依赖
- 同步调用——找回密码场景调用频率极低，且包装在 anyio.to_thread 中即可异步化
- mail_config.is_configured == False 时所有 send_* 直接抛 APIException("邮件服务暂未开通")
"""
import smtplib
from email.message import EmailMessage
from typing import Optional

from app.boot import APIException, logger, mail_config


def _ensure_configured() -> None:
    if not mail_config.is_configured:
        raise APIException(
            "邮件服务暂未开通，无法完成此操作。请联系管理员或使用其它方式。",
            code=10030,
            status_code=503,
        )


def send_mail(
    *,
    to: str,
    subject: str,
    body: str,
    html: Optional[str] = None,
) -> None:
    """发邮件——失败抛 APIException(code=10031)。SMTP 未配置时 _ensure_configured 抛 503。"""
    _ensure_configured()

    msg = EmailMessage()
    msg["From"] = mail_config.sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")

    try:
        if mail_config.use_ssl:
            smtp = smtplib.SMTP_SSL(mail_config.host, mail_config.port, timeout=15)
        else:
            smtp = smtplib.SMTP(mail_config.host, mail_config.port, timeout=15)

        with smtp as conn:
            conn.ehlo()
            if mail_config.use_tls and not mail_config.use_ssl:
                conn.starttls()
                conn.ehlo()
            if mail_config.username:
                conn.login(mail_config.username, mail_config.password)
            conn.send_message(msg)
    except APIException:
        raise
    except Exception as e:
        logger.error(f"send_mail failed to={to} subject={subject!r}: {type(e).__name__}: {e}")
        raise APIException("邮件发送失败，请稍后重试", code=10031, status_code=502)

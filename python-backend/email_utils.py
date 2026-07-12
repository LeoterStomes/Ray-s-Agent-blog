"""邮件发送工具 — 通过 SMTP 发送邮箱验证码"""
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_NAME


def send_code(to_email: str, code: str):
    """异步发送验证码邮件（在独立线程中执行，不阻塞请求）"""
    t = threading.Thread(target=_send_sync, args=(to_email, code), daemon=True)
    t.start()


def _send_sync(to_email: str, code: str):
    subject = f"【Ray的垃圾站】邮箱验证码: {code}"
    html = f"""\
<html><body style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:24px">
  <h2 style="color:#5b7bff">Ray的垃圾站</h2>
  <p>你的验证码是：</p>
  <div style="font-size:28px;font-weight:700;letter-spacing:6px;color:#1a1a2e;
              background:#f0f3ff;padding:16px 24px;border-radius:8px;text-align:center;margin:16px 0">
    {code}
  </div>
  <p style="color:#888;font-size:13px">验证码 5 分钟内有效，请勿转发给他人。</p>
  <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
  <p style="color:#aaa;font-size:12px">如非本人操作，请忽略此邮件。</p>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((SMTP_FROM_NAME, SMTP_USER))
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, [to_email], msg.as_string())
        server.quit()
    except Exception as e:
        print(f"[EMAIL] 发送失败: {to_email} - {e}")
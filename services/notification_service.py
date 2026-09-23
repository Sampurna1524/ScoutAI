import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

from models.job import Job

# Load .env variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)


class NotificationService:

    @staticmethod
    def is_configured() -> bool:
        user = os.getenv("SMTP_USER", "").strip()
        pwd = os.getenv("SMTP_PASS", "").strip()
        return bool(user and pwd)

    @staticmethod
    def get_default_recipient() -> str:
        return os.getenv("NOTIFICATION_DEFAULT_RECIPIENT", "").strip() or os.getenv("SMTP_USER", "").strip()

    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str, text_content: str = "") -> bool:
        host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
        port = int(os.getenv("SMTP_PORT", "587").strip() or 587)
        user = os.getenv("SMTP_USER", "").strip()
        pwd = os.getenv("SMTP_PASS", "").strip()

        if not user or not pwd:
            print("[NotificationService] SMTP credentials not set. Skipping email dispatch.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"ScoutAI <{user}>"
        msg["To"] = to_email

        if text_content:
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
        if html_content:
            msg.attach(MIMEText(html_content, "html", "utf-8"))

        try:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(user, pwd)
                server.sendmail(user, [to_email], msg.as_string())
            print(f"[NotificationService] Successfully sent notification email to {to_email}")
            return True
        except Exception as e:
            print(f"[NotificationService] Failed to send email to {to_email}: {e}")
            return False

    @staticmethod
    def send_top_matches(
        recipient: str,
        query: str,
        jobs: List[Job],
        candidate_profile: Optional[Dict[str, Any]] = None,
        total_discovered: int = 0,
    ) -> bool:
        if not jobs:
            return False

        # Pick top 5 jobs
        top_5 = jobs[:5]

        # Extract Candidate Name if available
        cand_name = (candidate_profile.get("name") or "Candidate") if candidate_profile else "Job Hunter"
        cand_headline = (candidate_profile.get("headline") or "") if candidate_profile else ""

        subject = f"⚡ ScoutAI Top 5 Job Matches: {query}"

        # Generate HTML content
        job_cards_html = []
        for idx, job in enumerate(top_5, 1):
            exp_text = ""
            if job.experience:
                exp_text = job.experience
            elif job.experience_years is not None:
                exp_text = "Fresher" if job.experience_years == 0 else f"{int(job.experience_years)} yrs exp"

            score_badge = ""
            if job.match_score is not None:
                score_color = "#10b981" if job.match_score >= 80 else "#38bdf8"
                score_badge = f"""
                <span style="background: rgba(16, 185, 129, 0.18); border: 1px solid {score_color}; color: {score_color}; font-weight: 700; font-size: 13px; padding: 4px 10px; border-radius: 6px; display: inline-block;">
                    🎯 {job.match_score}% Match
                </span>
                """

            badges_html = []
            if exp_text:
                badges_html.append(f'<span style="background: #1e293b; color: #34d399; font-size: 12px; padding: 3px 8px; border-radius: 4px; margin-right: 6px;">⏱️ {exp_text}</span>')
            if job.location:
                badges_html.append(f'<span style="background: #1e293b; color: #7dd3fc; font-size: 12px; padding: 3px 8px; border-radius: 4px; margin-right: 6px;">📍 {job.location}</span>')
            if job.work_mode:
                badges_html.append(f'<span style="background: #1e293b; color: #d8b4fe; font-size: 12px; padding: 3px 8px; border-radius: 4px; margin-right: 6px;">🌐 {job.work_mode}</span>')

            # Matched and missing skills
            skill_chips = []
            if job.matched_skills:
                for s in job.matched_skills[:5]:
                    skill_chips.append(f'<span style="background: rgba(16, 185, 129, 0.2); color: #34d399; font-size: 11px; padding: 2px 6px; border-radius: 4px; margin-right: 4px; display: inline-block;">✓ {s}</span>')
            if job.missing_skills:
                for s in job.missing_skills[:3]:
                    skill_chips.append(f'<span style="background: rgba(248, 113, 113, 0.15); color: #fca5a5; font-size: 11px; padding: 2px 6px; border-radius: 4px; margin-right: 4px; display: inline-block;">✗ {s}</span>')
            if not skill_chips and job.skills:
                for s in job.skills[:5]:
                    skill_chips.append(f'<span style="background: #1e293b; color: #94a3b8; font-size: 11px; padding: 2px 6px; border-radius: 4px; margin-right: 4px; display: inline-block;">{s}</span>')

            match_summary_html = ""
            if job.match_summary:
                match_summary_html = f'<p style="margin: 8px 0; font-size: 12.5px; color: #cbd5e1; font-style: italic;">💡 {job.match_summary}</p>'

            desc_snippet = (job.description[:220] + "...") if job.description else ""

            card = f"""
            <div style="background: #182234; border: 1px solid #27354f; border-radius: 12px; padding: 18px 20px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                    <div>
                        <h3 style="margin: 0 0 4px; font-size: 17px; color: #ffffff; font-weight: 700;">#{idx}. {job.title}</h3>
                        <div style="color: #34d399; font-size: 14px; font-weight: 600;">🏢 {job.company or "Verified Employer"}</div>
                    </div>
                    {score_badge}
                </div>
                <div style="margin: 8px 0;">
                    {''.join(badges_html)}
                </div>
                {match_summary_html}
                <div style="margin: 8px 0;">
                    {''.join(skill_chips)}
                </div>
                {f'<p style="color: #94a3b8; font-size: 13px; line-height: 1.5; margin: 8px 0;">{desc_snippet}</p>' if desc_snippet else ''}
                <div style="margin-top: 14px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px;">
                    <span style="color: #64748b; font-size: 12px;">Source: {job.source or "Direct Portal"}</span>
                    <a href="{job.apply_url}" style="background: #10b981; color: #052216; text-decoration: none; padding: 8px 16px; border-radius: 6px; font-weight: 700; font-size: 13px; display: inline-block;">View Job Posting →</a>
                </div>
            </div>
            """
            job_cards_html.append(card)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; color: #f0f4fc; margin: 0; padding: 24px 12px; }}
                .container {{ max-width: 650px; margin: 0 auto; background-color: #121826; border: 1px solid #27354f; border-radius: 16px; padding: 28px; }}
                .header {{ border-bottom: 1px solid #27354f; padding-bottom: 18px; margin-bottom: 22px; }}
                .brand {{ display: inline-block; background: #10b981; color: #062417; font-weight: 800; padding: 4px 10px; border-radius: 8px; font-size: 16px; margin-bottom: 8px; }}
                h1 {{ margin: 6px 0 2px; font-size: 22px; color: #ffffff; }}
                .meta {{ color: #94a3b8; font-size: 13.5px; }}
                .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 24px; border-top: 1px solid #27354f; padding-top: 16px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="brand">⚡ ScoutAI</div>
                    <h1>Top 5 Tailored Job Matches</h1>
                    <div class="meta">
                        Search query: <strong>{query}</strong> &bull; Total Discovered: <strong>{total_discovered or len(jobs)}</strong>
                        {f'<br>Prepared for: <strong>{cand_name}</strong> {f"({cand_headline})" if cand_headline else ""}' if candidate_profile else ''}
                    </div>
                </div>

                <div class="cards-list">
                    {''.join(job_cards_html)}
                </div>

                <div class="footer">
                    ScoutAI Autonomous Job Hunter &bull; Delivered automatically to {recipient}
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text fallback
        text_lines = [
            f"⚡ ScoutAI Top 5 Job Matches for '{query}'",
            f"Total jobs discovered: {total_discovered or len(jobs)}",
            "-" * 50,
        ]
        for idx, job in enumerate(top_5, 1):
            score_str = f" [{job.match_score}% Match]" if job.match_score is not None else ""
            text_lines.append(f"\n#{idx}. {job.title}{score_str}")
            text_lines.append(f"Company: {job.company or 'Direct Employer'}")
            if job.location: text_lines.append(f"Location: {job.location}")
            if job.match_summary: text_lines.append(f"Summary: {job.match_summary}")
            text_lines.append(f"Apply Link: {job.apply_url}")

        text_content = "\n".join(text_lines)

        return NotificationService.send_email(recipient, subject, html, text_content)

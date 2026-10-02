import re
from typing import Optional
from urllib.parse import urlparse

from models.job import Job
from models.scout_session import ScoutSession
from models.verification_request import VerificationRequest

URL_LOGIN_HINTS = (
    "/login",
    "/signin",
    "/sign-in",
    "/authwall",
    "/checkpoint",
    "/account/login",
    "login.",
    "accounts.google.com",
    "login.microsoftonline",
)

URL_VERIFY_HINTS = (
    "/captcha",
    "challenge",
    "/blocked",
    "cdn-cgi/challenge",
)

CAPTCHA_PATTERNS = [
    r"verify you(?:'|’)re human",
    r"verify you are human",
    r"verify that you are human",
    r"are you a robot",
    r"i(?:'|’)m not a robot",
    r"\bcaptcha\b",
    r"unusual traffic",
    r"attention required",
    r"checking your browser",
    r"just a moment[.\s]",
    r"enable javascript and cookies",
    r"cf-browser-verification",
    r"needs to review the security",
    r"confirm you are human",
]

LOGIN_PATTERNS = [
    r"sign in to continue",
    r"log in to continue",
    r"please (?:log|sign) in",
    r"log in to (?:view|see|continue|access)",
    r"sign in to (?:view|see|continue|access)",
    r"join to view",
    r"create an account to (?:continue|view|see)",
    r"you must (?:log|sign) in",
    r"login required",
    r"sign in with",
]


class VerificationService:

    @staticmethod
    def detect_from_content(url: str, text: str) -> Optional[str]:
        url_l = (url or "").lower()
        text_l = (text or "").lower()
        compact = re.sub(r"\s+", " ", text_l).strip()

        if any(hint in url_l for hint in URL_VERIFY_HINTS):
            return "human verification"

        if any(hint in url_l for hint in URL_LOGIN_HINTS):
            return "login required"

        for pattern in CAPTCHA_PATTERNS:
            if re.search(pattern, compact):
                return "human verification"

        login_hits = sum(1 for pattern in LOGIN_PATTERNS if re.search(pattern, compact))
        short_page = len(compact) < 1800

        if login_hits >= 2 or (login_hits >= 1 and short_page):
            return "login required"

        if not compact:
            return None

        return None

    @staticmethod
    def detect_from_page(page, url: str, text: str) -> Optional[str]:
        try:
            captcha_frames = page.locator(
                "iframe[src*='recaptcha'], iframe[src*='hcaptcha'], "
                "iframe[src*='challenges.cloudflare.com'], iframe[title*='Cloudflare']"
            ).count()
            if captcha_frames > 0:
                return "human verification"
        except Exception:
            pass

        content_reason = VerificationService.detect_from_content(url, text)
        if content_reason:
            return content_reason

        try:
            password_fields = page.locator("input[type='password']").count()
            if password_fields > 0 and len((text or "").strip()) < 2500:
                return "login required"
        except Exception:
            pass

        return None

    @staticmethod
    def enqueue(
        session: ScoutSession,
        url: str,
        reason: str,
        tab_index: int,
        title: str = "",
    ) -> VerificationRequest:
        task = VerificationRequest(
            site=urlparse(url).netloc,
            url=url,
            reason=reason,
            tab_index=tab_index,
            title=title,
            status="pending",
        )
        with session.lock:
            session.pending_verifications.append(task)
        session.append_event(
            "verification_needed",
            f"{reason.capitalize()} on {task.site}",
            {"task_id": task.task_id, "url": url, "reason": reason},
        )
        session.wake.set()
        return task

    @staticmethod
    def get_task(session: ScoutSession, task_id: str) -> Optional[VerificationRequest]:
        with session.lock:
            for task in session.pending_verifications:
                if task.task_id == task_id:
                    return task
        return None

    @staticmethod
    def set_status(session: ScoutSession, task_id: str, status: str) -> VerificationRequest:
        task = VerificationService.get_task(session, task_id)
        if task is None:
            raise KeyError(task_id)
        if task.status in ("declined", "completed") and status != task.status:
            raise ValueError(f"Task already {task.status}")
        with session.lock:
            task.status = status
        session.append_event(
            "verification_update",
            f"Task {status}: {task.site}",
            {"task_id": task.task_id, "status": status},
        )
        session.wake.set()
        return task

    @staticmethod
    def mark_skipped_job(session: ScoutSession, task: VerificationRequest):
        job = Job(
            title=task.title,
            apply_url=task.url,
            source=task.site,
            status="skipped",
            error=f"User declined {task.reason}",
        )
        with session.lock:
            session.jobs.append(job)

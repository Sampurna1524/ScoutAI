from services.verification_service import VerificationService


def test_detects_login_wall():
    reason = VerificationService.detect_from_content(
        "https://www.linkedin.com/authwall",
        "Sign in to continue to LinkedIn",
    )
    assert reason == "login required"


def test_detects_human_verification():
    reason = VerificationService.detect_from_content(
        "https://example.com/jobs/123",
        "Verify you are human. This helps us keep out bots.",
    )
    assert reason == "human verification"


def test_ignores_normal_job_page():
    text = (
        "Senior Python Engineer at Acme. You will design APIs and train models. "
        "Apply on the company careers site. Experience with FastAPI required."
    )
    reason = VerificationService.detect_from_content(
        "https://jobs.acme.com/python-engineer",
        text,
    )
    assert reason is None

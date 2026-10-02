import time
import re
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse

from models.job import Job
from services.profile_service import CandidateProfile


class AutoApplyService:

    @staticmethod
    def detect_apply_type(page, url: str) -> str:
        """
        Determines the application type on the given page:
        - "easy_apply": LinkedIn Easy Apply button present
        - "greenhouse": Greenhouse application form present
        - "lever": Lever application form present
        - "ashby": Ashby application form present
        - "external": Requires external company portal redirect
        """
        try:
            url_lower = url.lower()
            if "linkedin.com" in url_lower:
                # Check for Easy Apply button
                easy_apply_btn = page.locator("button.jobs-apply-button, button[aria-label*='Easy Apply'], button:has-text('Easy Apply')").first
                if easy_apply_btn.is_visible(timeout=2000):
                    return "easy_apply"
                return "external"

            if "greenhouse.io" in url_lower or page.locator("#application_form, form#apply_form").count() > 0:
                return "greenhouse"

            if "lever.co" in url_lower or page.locator(".application-form, form#application-form").count() > 0:
                return "lever"

            if "ashbyhq.com" in url_lower or page.locator("form:has-text('Submit Application')").count() > 0:
                return "ashby"

            # Check for generic apply button on page
            apply_btn = page.locator("a:has-text('Apply'), button:has-text('Apply')").first
            if apply_btn.is_visible(timeout=1000):
                return "ats"
        except Exception:
            pass

        return "external"

    @staticmethod
    def apply_to_job(page, job: Job, candidate: CandidateProfile, mode: str = "review") -> Tuple[Job, str]:
        """
        Executes auto-application to a job:
        - mode: "review" (fills form and pauses at review step) or "auto" (submits application)
        Returns (updated_job, message)
        """
        job.application_status = "applying"
        url = job.apply_url

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(1500)
        except Exception as e:
            job.application_status = "failed"
            job.application_notes = f"Failed to load job page: {e}"
            return job, job.application_notes

        apply_type = AutoApplyService.detect_apply_type(page, url)
        job.apply_type = apply_type

        if apply_type == "easy_apply":
            return AutoApplyService._apply_linkedin(page, job, candidate, mode)
        elif apply_type in ("greenhouse", "lever", "ashby", "ats"):
            return AutoApplyService._apply_ats(page, job, candidate, mode)
        else:
            job.application_status = "review_ready"
            job.application_notes = "External application link (manual submission required on company portal)."
            return job, job.application_notes

    @staticmethod
    def _apply_linkedin(page, job: Job, candidate: CandidateProfile, mode: str = "review") -> Tuple[Job, str]:
        try:
            # Click Easy Apply button
            apply_btn = page.locator("button.jobs-apply-button, button[aria-label*='Easy Apply'], button:has-text('Easy Apply')").first
            if not apply_btn.is_visible(timeout=3000):
                job.application_status = "review_ready"
                job.application_notes = "Easy Apply button not currently visible or already applied."
                return job, job.application_notes

            apply_btn.click()
            page.wait_for_timeout(1500)

            # Check if modal is open
            modal = page.locator(".jobs-easy-apply-modal, div[role='dialog']").first
            if not modal.is_visible(timeout=4000):
                job.application_status = "review_ready"
                job.application_notes = "Application dialog opened externally."
                return job, job.application_notes

            # Loop through multi-step dialog
            max_steps = 6
            for step in range(max_steps):
                page.wait_for_timeout(800)
                AutoApplyService._fill_form_fields(page, candidate)

                # Look for 'Review' button
                review_btn = page.locator("button[aria-label*='Review your application'], button:has-text('Review')").first
                if review_btn.is_visible(timeout=1000):
                    review_btn.click()
                    page.wait_for_timeout(1000)

                    if mode == "review":
                        try:
                            page.bring_to_front()
                        except Exception:
                            pass
                        job.application_status = "review_ready"
                        job.application_notes = "Application auto-filled! Please review and submit in browser."
                        return job, job.application_notes
                    else:
                        # Full auto submit
                        submit_btn = page.locator("button[aria-label*='Submit application'], button:has-text('Submit application')").first
                        if submit_btn.is_visible(timeout=2000):
                            submit_btn.click()
                            page.wait_for_timeout(2000)
                            job.application_status = "applied"
                            job.applied_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                            job.application_notes = "Application submitted automatically via LinkedIn Easy Apply."
                            return job, job.application_notes

                # Check for 'Next' button
                next_btn = page.locator("button[aria-label*='Continue to next step'], button:has-text('Next')").first
                if next_btn.is_visible(timeout=1000):
                    next_btn.click()
                    continue

                # Check for direct 'Submit application' button
                submit_btn = page.locator("button[aria-label*='Submit application'], button:has-text('Submit application')").first
                if submit_btn.is_visible(timeout=1000):
                    if mode == "review":
                        try:
                            page.bring_to_front()
                        except Exception:
                            pass
                        job.application_status = "review_ready"
                        job.application_notes = "Application auto-filled! Please review and submit in browser."
                        return job, job.application_notes
                    else:
                        submit_btn.click()
                        page.wait_for_timeout(2000)
                        job.application_status = "applied"
                        job.applied_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                        job.application_notes = "Application submitted automatically via LinkedIn Easy Apply."
                        return job, job.application_notes

                break

            job.application_status = "review_ready"
            job.application_notes = "Form auto-filled. Complete any remaining questions in browser."
            return job, job.application_notes

        except Exception as e:
            job.application_status = "review_ready"
            job.application_notes = f"Auto-fill partial: {e}"
            return job, job.application_notes

    @staticmethod
    def _apply_ats(page, job: Job, candidate: CandidateProfile, mode: str = "review") -> Tuple[Job, str]:
        try:
            page.wait_for_timeout(1000)
            AutoApplyService._fill_form_fields(page, candidate)

            # In review mode, leave the filled form in the browser tab
            if mode == "review":
                try:
                    page.bring_to_front()
                except Exception:
                    pass
                job.application_status = "review_ready"
                job.application_notes = "ATS application form filled! Please inspect and submit."
                return job, job.application_notes
            else:
                # Try finding submit button
                submit_btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Submit Application'), button:has-text('Apply')").first
                if submit_btn.is_visible(timeout=2000):
                    submit_btn.click()
                    page.wait_for_timeout(2000)
                    job.application_status = "applied"
                    job.applied_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                    job.application_notes = "Application submitted automatically on ATS portal."
                    return job, job.application_notes

                job.application_status = "review_ready"
                job.application_notes = "ATS form filled. Click submit in browser."
                return job, job.application_notes

        except Exception as e:
            job.application_status = "review_ready"
            job.application_notes = f"ATS fill notice: {e}"
            return job, job.application_notes

    @staticmethod
    def _fill_form_fields(page, candidate: CandidateProfile):
        """
        Fills standard text inputs, phone, email, name, URLs, and radio buttons.
        """
        if not candidate:
            return

        name_parts = candidate.name.split() if candidate.name else ["Candidate"]
        first_name = name_parts[0] if name_parts else "Candidate"
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        # Fill First Name / Full Name
        AutoApplyService._safe_fill(page, "input[name*='first_name' i], input[id*='first_name' i], input[autocomplete='given-name']", first_name)
        AutoApplyService._safe_fill(page, "input[name*='last_name' i], input[id*='last_name' i], input[autocomplete='family-name']", last_name)
        AutoApplyService._safe_fill(page, "input[name*='name' i]:not([name*='first']):not([name*='last']), input[id*='name' i]:not([id*='first']):not([id*='last']), input[autocomplete='name']", candidate.name)

        # Fill Email
        if candidate.email:
            AutoApplyService._safe_fill(page, "input[type='email'], input[name*='email' i], input[id*='email' i]", candidate.email)

        # Fill Phone
        if candidate.phone:
            AutoApplyService._safe_fill(page, "input[type='tel'], input[name*='phone' i], input[id*='phone' i], input[name*='mobile' i]", candidate.phone)

        # Fill LinkedIn URL
        if candidate.linkedin_url:
            AutoApplyService._safe_fill(page, "input[name*='linkedin' i], input[id*='linkedin' i], input[placeholder*='linkedin' i]", candidate.linkedin_url)

        # Fill GitHub / Portfolio URL
        if candidate.github_url:
            AutoApplyService._safe_fill(page, "input[name*='github' i], input[id*='github' i]", candidate.github_url)
        if candidate.portfolio_url:
            AutoApplyService._safe_fill(page, "input[name*='website' i], input[name*='portfolio' i]", candidate.portfolio_url)

        # Handle numeric / experience questions
        if candidate.experience_years is not None:
            exp_val = str(int(candidate.experience_years))
            AutoApplyService._safe_fill_by_label_pattern(page, r"years?\s+of\s+experience|how\s+many\s+years", exp_val)

        # Handle Work Authorization Radios (Yes / No)
        AutoApplyService._safe_select_radio_by_label(page, r"authorized\s+to\s+work|legally\s+authorized", "yes")
        AutoApplyService._safe_select_radio_by_label(page, r"require\s+sponsorship|visa\s+sponsorship", "no")

    @staticmethod
    def _safe_fill(page, selector: str, value: str):
        if not value:
            return
        try:
            inputs = page.locator(selector).all()
            for inp in inputs:
                if inp.is_visible(timeout=500):
                    curr = inp.input_value()
                    if not curr or not curr.strip():
                        inp.fill(value)
        except Exception:
            pass

    @staticmethod
    def _safe_fill_by_label_pattern(page, label_pattern: str, value: str):
        try:
            labels = page.locator("label").all()
            for lbl in labels:
                txt = lbl.inner_text()
                if re.search(label_pattern, txt, re.I):
                    target_id = lbl.get_attribute("for")
                    if target_id:
                        inp = page.locator(f"#{target_id}")
                        if inp.is_visible() and not inp.input_value().strip():
                            inp.fill(value)
                    else:
                        inp = lbl.locator("xpath=following::input[1]").first
                        if inp.is_visible() and not inp.input_value().strip():
                            inp.fill(value)
        except Exception:
            pass

    @staticmethod
    def _safe_select_radio_by_label(page, question_pattern: str, desired_value: str = "yes"):
        try:
            fieldsets = page.locator("fieldset, .fb-radio, .jobs-easy-apply-form-section").all()
            for fs in fieldsets:
                txt = fs.inner_text()
                if re.search(question_pattern, txt, re.I):
                    radios = fs.locator("input[type='radio'], label").all()
                    for r in radios:
                        r_txt = r.inner_text().strip().lower() if r.evaluate("el => el.tagName") == "LABEL" else r.get_attribute("value") or ""
                        if desired_value in r_txt:
                            r.click()
                            break
        except Exception:
            pass

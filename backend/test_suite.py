import unittest
from services.verification_service import VerificationService
from services.link_extractor_service import LinkExtractorService
from services.browser_service import BrowserService
from services.profile_service import ProfileService, CandidateProfile
from models.job import Job

class TestScoutFeatures(unittest.TestCase):

    def test_verification_detection(self):
        self.assertEqual(
            VerificationService.detect_from_content("https://www.linkedin.com/authwall", "Sign in to continue to LinkedIn"),
            "login required"
        )
        self.assertEqual(
            VerificationService.detect_from_content("https://example.com/jobs/123", "Verify you are human. This helps us keep out bots."),
            "human verification"
        )
        self.assertIsNone(
            VerificationService.detect_from_content("https://jobs.acme.com/python-engineer", "Senior Python Engineer at Acme. Experience with FastAPI required.")
        )

    def test_link_extractor_apex_domain_matching(self):
        page_url = "https://in.linkedin.com/jobs/python-jobs"
        dest_url = "https://www.linkedin.com/jobs/view/1234567890/"
        # Should be recognized as individual job posting
        self.assertTrue(LinkExtractorService.is_detail_url(dest_url))
        self.assertTrue(LinkExtractorService.is_listing_url(page_url))

    def test_link_extractor_ats_patterns(self):
        ats_urls = [
            "https://boards.greenhouse.io/stripe/jobs/12345",
            "https://jobs.lever.co/openai/abcdef",
            "https://jobs.ashbyhq.com/anthropic/xyz",
            "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/USA/Software-Engineer_JR123",
            "https://jobs.smartrecruiters.com/Square/123456789",
            "https://apply.workable.com/spotify/j/ABCDEF/",
        ]
        for url in ats_urls:
            self.assertTrue(LinkExtractorService.is_detail_url(url), f"Failed for {url}")

    def test_multi_queries_builder(self):
        queries = BrowserService.build_multi_queries("Python AI Engineer", {
            "role": "Python AI Engineer",
            "company": "OpenAI",
            "location": "San Francisco"
        })
        self.assertGreaterEqual(len(queries), 2)
        self.assertTrue(any("OpenAI" in q for q in queries))

        queries_general = BrowserService.build_multi_queries("Python AI Engineer", {
            "role": "Python AI Engineer",
            "location": "Mumbai",
            "skills": "PyTorch, FastAPI"
        })
        self.assertGreaterEqual(len(queries_general), 3)

    def test_candidate_profile_matching(self):
        cand = CandidateProfile(
            name="Alice Developer",
            headline="Senior Python AI Engineer",
            experience_years=5.0,
            skills=["Python", "FastAPI", "PyTorch", "Docker", "PostgreSQL"],
            location_preference="Mumbai"
        )

        job = Job(
            title="Senior Python AI Engineer",
            company="Tech Corp",
            location="Mumbai, India",
            experience_years=4.0,
            skills=["Python", "FastAPI", "PyTorch", "Kubernetes"],
            description="We are looking for a Senior Python Engineer with experience in FastAPI and PyTorch in Mumbai."
        )

        scored = ProfileService.evaluate_match(cand, job)
        self.assertIsNotNone(scored.match_score)
        self.assertGreaterEqual(scored.match_score, 80)
        self.assertIn("Python", scored.matched_skills)
        self.assertIn("FastAPI", scored.matched_skills)
        self.assertIn("PyTorch", scored.matched_skills)

    def test_notification_service_configuration(self):
        from services.notification_service import NotificationService
        self.assertTrue(NotificationService.is_configured())
        self.assertEqual(NotificationService.get_default_recipient(), "ai.scoutieee@gmail.com")

    def test_auto_apply_profile_contacts(self):
        sample_resume = """
        John Doe
        Senior AI Engineer
        Email: john.doe.ai@gmail.com
        Phone: +1 415-555-0199
        LinkedIn: https://linkedin.com/in/johndoe-ai
        Skills: Python, PyTorch, LangChain, FastAPI
        Experience: 4 years
        """
        profile = ProfileService._fallback_heuristic_parse(sample_resume)
        self.assertEqual(profile.email, "john.doe.ai@gmail.com")
        self.assertTrue("415-555-0199" in profile.phone or "4155550199" in profile.phone)
        self.assertIn("linkedin.com/in/johndoe-ai", profile.linkedin_url)
        self.assertIn("Python", profile.skills)

    def test_auto_apply_job_model_fields(self):
        job = Job(
            title="Software Engineer",
            company="OpenAI",
            apply_url="https://jobs.lever.co/openai/123",
            apply_type="lever",
            application_status="unapplied"
        )
        self.assertEqual(job.apply_type, "lever")
        self.assertEqual(job.application_status, "unapplied")
        job.application_status = "review_ready"
        self.assertEqual(job.application_status, "review_ready")

    def test_notification_hunt_results_modes(self):
        from unittest.mock import patch
        from services.notification_service import NotificationService

        jobs = [
            Job(title="AI Engineer", company="Co1", apply_url="https://co1.com/job1", match_score=95, application_status="applied"),
            Job(title="ML Engineer", company="Co2", apply_url="https://co2.com/job2", match_score=90, application_status="review_ready"),
            Job(title="Python Dev", company="Co3", apply_url="https://co3.com/job3", match_score=85, application_status="unapplied"),
            Job(title="Data Scientist", company="Co4", apply_url="https://co4.com/job4", match_score=80, application_status="unapplied"),
            Job(title="Backend Eng", company="Co5", apply_url="https://co5.com/job5", match_score=75, application_status="unapplied"),
            Job(title="Full Stack", company="Co6", apply_url="https://co6.com/job6", match_score=70, application_status="unapplied"),
        ]

        with patch.object(NotificationService, "send_email", return_value=True) as mock_send:
            # 1. Normal mode (auto_apply_mode = "off") -> sends Top 5 Matches
            res1 = NotificationService.send_hunt_results(
                recipient="test@example.com",
                query="AI Engineer",
                jobs=jobs,
                auto_apply_mode="off"
            )
            self.assertTrue(res1)
            subject1 = mock_send.call_args[0][1]
            self.assertIn("Top 5 Job Matches", subject1)

            # 2. Auto-Apply mode ("review" or "auto") with applied jobs -> sends Auto-Apply Report
            res2 = NotificationService.send_hunt_results(
                recipient="test@example.com",
                query="AI Engineer",
                jobs=jobs,
                auto_apply_mode="review"
            )
            self.assertTrue(res2)
            subject2 = mock_send.call_args[0][1]
            self.assertIn("Application Report", subject2)

if __name__ == "__main__":
    unittest.main()

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

if __name__ == "__main__":
    unittest.main()

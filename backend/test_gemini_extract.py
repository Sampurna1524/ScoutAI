from playwright.sync_api import sync_playwright

from services.gemini_service import GeminiService


url = "https://in.indeed.com/q-python-ai-l-mumbai,-maharashtra-jobs.html"

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    page.goto(url, wait_until="domcontentloaded")

    page.wait_for_timeout(3000)

    text = page.locator("body").inner_text()

    browser.close()

print(text[:2000])

job = GeminiService.extract_job(text)

print(type(job))
print()

print(job)
print()

print(job.title)
print(job.company)
print(job.skills)
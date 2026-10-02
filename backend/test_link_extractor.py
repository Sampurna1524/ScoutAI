from playwright.sync_api import sync_playwright

from services.link_extractor_service import LinkExtractorService

url = "https://in.indeed.com/q-python-ai-l-mumbai,-maharashtra-jobs.html"

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    page.goto(url)

    links = LinkExtractorService.extract_job_links(page, url)

    browser.close()

print(f"Found {len(links)} links.\n")

for link in links:
    print(link)
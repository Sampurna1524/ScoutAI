from services.crawler_service import CrawlerService

url = "https://in.indeed.com/q-python-ai-l-mumbai,-maharashtra-jobs.html"

text = CrawlerService.get_page_text(url)

print(text[:3000])
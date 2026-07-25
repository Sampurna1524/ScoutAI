from services.crawler_service import CrawlerService

text = CrawlerService.get_page_text(
    "https://www.naukri.com/ai-engineer-jobs-in-mumbai"
)

print(text[:3000])
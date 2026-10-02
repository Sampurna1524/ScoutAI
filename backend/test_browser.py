from services.browser_service import BrowserService

results = BrowserService.search_google(
    "Python AI Engineer jobs in Mumbai"
)

for result in results:
    print(result.title)
    print(result.url)
    print("-" * 60)
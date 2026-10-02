# ScoutAI

## Project Structure

.
├── README.md
├── requirements.txt
├── backend
│   ├── .env
│   ├── .git
│   ├── __pycache__
│   ├── agents
│   │   ├── base_agent.py
│   │   ├── job_agent.py
│   │   └── __pycache__
│   ├── models
│   │   ├── event.py
│   │   ├── job.py
│   │   ├── scout_session.py
│   │   ├── search_result.py
│   │   ├── verification_request.py
│   │   └── __pycache__
│   ├── main.py
│   ├── database
│   ├── routers
│   │   ├── search_router.py
│   │   └── __pycache__
│   ├── services
│   │   ├── browser_service.py
│   │   ├── crawler_service.py
│   │   ├── extractor_service.py
│   │   ├── link_extractor_service.py
│   │   ├── llm
│   │   │   ├── __init__.py
│   │   │   ├── llm_service.py
│   │   │   ├── provider.py
│   │   │   ├── provider_factory.py
│   │   │   └── providers
│   │   │       ├── gemini_provider.py
│   │   │       ├── groq_provider.py
│   │   │       └── __init__.py
│   │   ├── search_service.py
│   │   └── __pycache__
│   ├── test_browser.py
│   ├── test_crawler.py
│   ├── test_gemini.py
│   ├── test_gemini_extract.py
│   ├── test_job_agent.py
│   ├── test_link_extractor.py
│   ├── utils
│   └── __pycache__
├── frontend
└── venv

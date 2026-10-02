import inspect
from services.llm.llm_service import LLMService
from models.scout_session import ScoutSession
from services.llm.registry import get_provider_classes

print('LLMService.extract_job signature:', inspect.signature(LLMService.extract_job))
print('ScoutSession has events attr:', hasattr(ScoutSession(), 'events'))
print('Registered providers:', [c.__name__ for c in get_provider_classes()])

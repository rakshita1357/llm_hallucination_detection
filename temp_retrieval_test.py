from modules import metrics
from modules.retrieval import retrieve_for_claims

metrics.reset()
claim = {
    "id": "c1",
    "text": "Test claim",
    "self_confidence": 0.2,
    "needs_retrieval": True,
    "search_query": "sky",
    "evidence": []
}
result = retrieve_for_claims([claim])
print('Metrics after retrieval:', metrics.retrieval_calls)
print('Result:', result)

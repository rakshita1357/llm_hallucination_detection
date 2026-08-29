import json
from main import run_pipeline, PipelineRequest
req = PipelineRequest(question='What is the sky?', answer_text='The sky is blue.')
result = run_pipeline(req)
print(json.dumps(result, indent=2))

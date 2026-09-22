import json
from main import run_pipeline, PipelineRequest, get_metrics_history
req = PipelineRequest(question='test?', answer_text='Answer text.')
_ = run_pipeline(req)
print('History after run:', json.dumps(get_metrics_history(), indent=2))

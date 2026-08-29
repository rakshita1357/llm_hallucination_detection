from main import run_pipeline, PipelineRequest, get_metrics_history
req = PipelineRequest(question='Test?', answer_text='The sky is blue.')
result = run_pipeline(req)
print('Result keys:', result.keys())
print('Escalation rate:', result.get('escalation_rate'))
print('History after run:', get_metrics_history())

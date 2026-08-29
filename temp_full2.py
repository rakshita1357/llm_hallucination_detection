from main import run_pipeline, PipelineRequest
req = PipelineRequest(question='Test?', answer_text='The sky is blue.')
result = run_pipeline(req)
print(result)

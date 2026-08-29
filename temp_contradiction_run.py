from main import run_pipeline, PipelineRequest

req = PipelineRequest(question='', answer_text='The sky is blue. The sky is red.')
result = run_pipeline(req)
print(result)

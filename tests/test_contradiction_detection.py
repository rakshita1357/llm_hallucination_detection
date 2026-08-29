from main import run_pipeline, PipelineRequest

def test_contradiction_detection():
    req = PipelineRequest(question='', answer_text='The sky is blue. The sky is red.')
    result = run_pipeline(req)
    # All report entries should have internal_consistency_failure flagged
    for claim in result.get('report', []):
        assert claim.get('internal_consistency_failure') is True

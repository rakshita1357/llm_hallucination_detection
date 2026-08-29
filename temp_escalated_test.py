from modules import metrics
print('Before:', metrics.escalated_claims)
metrics.increment_escalated_claims(3)
print('After:', metrics.escalated_claims)

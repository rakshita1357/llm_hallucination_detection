import json
from main import get_metrics_history
print(json.dumps(get_metrics_history(), indent=2))

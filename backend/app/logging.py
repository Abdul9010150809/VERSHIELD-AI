import json
import os
from datetime import datetime
from agents.orchestrator import Orchestrator

RESULTS_FILE = "results.json"

def log_decision(evaluation_result: dict, metadata: dict = None):
    """
    Log the decision outcome to results.json, anonymizing PII.
    """
    # Anonymize metadata
    anonymized_metadata = Orchestrator.anonymize_stream(metadata or {})

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "decision": evaluation_result["decision"],
        "reasoning": evaluation_result["reasoning"],
        "vision_score": evaluation_result["vision_score"],
        "acoustic_score": evaluation_result["acoustic_score"],
        "transaction_amount": evaluation_result["transaction_amount"],
        "metadata": anonymized_metadata
    }

    # Load existing results
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            try:
                results = json.load(f)
            except json.JSONDecodeError:
                results = []
    else:
        results = []

    # Append new entry
    results.append(log_entry)

    # Save back
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
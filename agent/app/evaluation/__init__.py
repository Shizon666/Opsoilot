"""Agent evaluation (Phase 11 Legacy + C-4.3 V1 P0).

Legacy: ``cases.yaml``
V1 P0: ``v1/cases_c42.yaml``
Runner: ``python -m app.evaluation.runner --cases-file app/evaluation/v1/cases_c42.yaml``
"""

from app.evaluation.runner import load_cases, main, run_all

__all__ = ["load_cases", "main", "run_all"]

"""Agentic estimator package.

The orchestrator dependencies (LangGraph, etc.) are optional for lightweight
scripts that only need direct access to submodules. Importing the orchestrator
is attempted lazily so that tools without the heavier stack can still utilise
components such as EstimatorAgent.
"""

try:  # pragma: no cover - optional dependency wiring
    from .orchestrator.runner import generate_context_summary, run_agentic_pipeline  # noqa: F401
except ModuleNotFoundError as exc:  # pragma: no cover
    _IMPORT_ERROR = exc

    def _missing_orchestrator(*_args, **_kwargs):
        raise ModuleNotFoundError(
            "Optional orchestrator dependencies are not installed; install "
            "langgraph and related packages to enable this functionality."
        ) from _IMPORT_ERROR

    generate_context_summary = _missing_orchestrator  # type: ignore
    run_agentic_pipeline = _missing_orchestrator  # type: ignore

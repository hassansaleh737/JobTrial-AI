# JobTrial AI v3 changes

- Added `backend/job_compiler.py`: role signals, tasks tailored from validated work-sample blueprints, seeded additional tests, coverage explanations, professional deliverable templates with honest human-review status.
- Updated `backend/adaptive.py`: added binary F1, retrieval recall for RAG, forecast MAE, uptime reporting, and numeric model accuracy, alongside existing cases; accepts multi-statement Python and generated test variants.
- Updated `backend/docker_grader.py`: validates the same seeded cases as the bounded Python interpreter (for supported languages, when local Docker explicitly enabled).
- Updated `backend/engine.py`: dedicated accessible contact-form checks.
- Updated `backend/main.py`: `/api/analyze` uses new compiler, `professional` review endpoint, v3 health check, safe task ID validation.
- Updated `frontend/src/App.tsx`, `frontend/src/types.ts`, `frontend/src/styles.css`: skill coverage and exclusions, professional deliverable workspace, unscored manual-review result, v3 label, distinct task selection.
- Added `tests/test_dynamic_v3.py`; **22 backend tests passed** when built. Actual Hugging Face provider requests, local Docker runtimes and production React build not tested in this environment.

**Key limitations**: finite validated exercise templates, not unrestricted job-to-code generation; not all skills have automatic tests; Docker option is for local experiments only.

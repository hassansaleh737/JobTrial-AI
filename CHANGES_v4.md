# JobTrial AI v4 changes
- Five difficulty levels and an adjustable target intensity for each.
- Hugging Face required by default in UI, explicit offline demo switch.
- New `backend/ai_missions.py`: structured HF mission generation with validation and explanatory errors.
- New `backend/ai_numeric.py`: optional genuinely AI-authored numerical function challenge, AST-validated oracle and stored independent tests.
- `backend/docker_grader.py`: optional custom numeric grading for JS/TS/Java/C++/Go with restricted local Docker.
- `backend/main.py`: `POST /api/analyze` difficulty + AI flags, `POST /api/ai-coach` qualitative feedback, health version 4.0.0.
- `frontend/src/App.tsx`, `types.ts`, `styles.css`: difficulty selection, AI/Offline status, mission artifacts, coaching UI.
- `.env.example`: configuration guidance, no token included.
- `tests/test_ai_v4.py` and `tests/test_ai_numeric_v4.py`: mock-only HF tests and safe numeric evaluation.

Full AI model access requires an actual HF token and provider balance; we never bundle credentials.

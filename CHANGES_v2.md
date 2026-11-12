# JobTrial AI v2 — adaptive tasks and code evaluation

This upgrade changes task selection and the backend grading path without replacing the existing UI or the user's environment.

- `backend/adaptive.py`: interpret descriptions, select validated assignments for varied engineering roles, and choose language.
- `backend/safe_python.py`: bounded AST interpreter supporting variables, conditionals, loops, lists and multiple statements. **No Python exec/eval**.
- `backend/docker_grader.py`: optional local Docker grading for JavaScript, TypeScript, Java, C++, Go and full Python. **Do not deploy publicly**.
- `backend/main.py`: `/api/analyze` returns a dynamic trial; `/api/run` and `/api/submit` select the correct grader.
- `frontend/src/App.tsx` and `types.ts`: language selector, dynamically produced work trial, limitations displayed.
- `.env.example`: Docker opt-in settings.
- `RUN_FAST.bat`: starts the project using the **existing** Python environment, with no installation/build.
- `README_AR.md`: exact VS Code run instructions and example code.

**Known limitations**: Automated executable grading remains limited to validated task blueprints and the supported languages. JavaScript/TypeScript/Java/C++/Go need local Docker images. Py local AST interpretation isn't full Python. HF enhances role analysis but does not invent test harnesses. Existing frontend and SQL exercises are predefined, though selected from job requirements.

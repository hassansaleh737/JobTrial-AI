# V6 Slider and Task Rotation

- Adds `backend/alternate_contracts.py`: 15 trusted alternative challenge contracts and independent reference functions.
- Adds a `variation_index` request property, a selected challenge variant in task IDs, and alternate selection on adjacent intensity steps.
- Updates HF work brief generation to use the selected real verified challenge, rather than describing the wrong task.
- Adds a frontend `Switch next task` control, preserves the current environment and server.
- Keeps backward support for existing v5 task IDs.
- Adds regression tests for slider differences, starter scripts, and reference oracles.

This version has **two** tested contracts per level and track (15 original + 15 alternatives). This is not unlimited AI-generated code assessment; remaining roadmap is in README_V6_AR.md.

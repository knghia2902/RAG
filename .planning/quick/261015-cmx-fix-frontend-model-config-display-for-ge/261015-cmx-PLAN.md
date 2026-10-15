---
quick_id: 261015-cmx
type: quick
status: planned
files_modified:
  - frontend/src/app/(workspace)/configuration/page.tsx
must_haves:
  truths:
    - Frontend configuration page displays "Google Gemini API" when llm_provider is "gemini".
    - Frontend configuration page displays "Đã cấu hình" when gemini_configured is true.
  artifacts:
    - Updated frontend/src/app/(workspace)/configuration/page.tsx
---

# Quick Plan: Fix Frontend Model Config Display for Gemini

<objective>
Update the configuration page in the frontend to properly recognize Google Gemini as LLM Provider and display "Google Gemini API" and "Đã cấu hình" status when gemini_configured is true.
</objective>

<tasks>
<task type="auto">
  <name>Task 1: Update configuration page JSX to support Gemini provider and status</name>
  <files>frontend/src/app/(workspace)/configuration/page.tsx</files>
  <action>
    Update llm_provider check to include "gemini" -> "Google Gemini API".
    Update API key status check to recognize gemini_configured.
    Rebuild frontend container to serve the updated assets.
  </action>
  <verify>
    <automated>docker compose up -d --build frontend</automated>
  </verify>
  <done>Frontend accurately reflects Gemini provider and active key configuration.</done>
</task>
</tasks>

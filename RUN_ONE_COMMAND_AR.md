# JobTrial AI — تشغيل الموقع بأمر واحد على VS Code

## أول تشغيل على Windows
1. فك ضغط ZIP وافتح فولدر `JobTrial_AI` في VS Code.
2. لازم يكون Python 3.10+ وNode.js/npm مثبتين.
3. ملف `.env` بيتكوّن تلقائيًا من `.env.example` أول مرة تشغّل الملف. أضف `HF_TOKEN=hf_...` بنفسك إذا عايز تحليل Hugging Face. لا تشارك التوكن.
4. من VS Code Terminal (PowerShell) وإنت في فولدر `JobTrial_AI` شغّل:

```powershell
.\START_ONE_COMMAND.bat
```

5. افتح `http://127.0.0.1:8000` — الواجهة والـAPI على نفس العنوان.
6. للإيقاف اضغط Ctrl+C في نفس Terminal.

## مهم
- في أول مرة التشغيل ينزّل pip/npm packages (محتاج إنترنت).
- الملف يبني React بـ `npm run build` ثم FastAPI يقدّم مجلد `frontend/dist`.
- لما تعدل الواجهة، أوقف السيرفر وأعد تشغيل الملف لإعادة بناء React.
- لو كنت مشغل السيرفر القديم على 8000، اقفله أولًا.
- تقدر تستعمل التطوير العادي (2 terminals) لو عايز hot reload، لكن الملف ده للوضع المبسط.
- Swagger API: http://127.0.0.1:8000/docs
- الاختبار: `.\.venv\Scripts\python.exe -m pytest -q` من جذر المشروع بعد تثبيت الاختبارات إذا كانت متاحة.

## الملفات الجديدة/المعدلة
- `backend/main.py`: إضافة StaticFiles في نهاية الملف بعد جميع endpoints.
- `START_ONE_COMMAND.bat`: بيجهّز البيئتين ويبني الواجهة ويشغّل السيرفر.
- `frontend/vite.config.ts`: **لا يحتاج تعديل**؛ Proxy الحالي خاص بوضع `npm run dev` فقط.
- `.env.example`: موجود؛ `.env` يتولد عند التشغيل.

**أمان:** هذه نسخة تجريبية لتقييم كود الطلاب؛ لا ترفع خدمة تنفيذ كود عامة للإنترنت بدون عزل قوي وقيود موارد/شبكات.

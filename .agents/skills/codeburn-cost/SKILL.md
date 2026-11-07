---
name: codeburn-cost
description: "Учёт токенов и расчётной стоимости локальных сеансов Codex через установленный CodeBurn; проверка наличия журналов и осторожная интерпретация оценок."
---

# CodeBurn cost

Use this skill when the user asks about token usage, estimated AI coding cost,
or whether local agent history is available. This is the read-only integration;
it does not install the Caveman proxy or connect any account.

Resolve the repository root from this file (`../../..`). Run:

```bash
python3 tools/codeburn.py doctor
python3 tools/codeburn.py today
```

The wrapper uses a pinned, project-local CodeBurn CLI and filters reports to Codex.
Other agents' usage is outside this wrapper's reporting scope. If the runtime is missing,
report the missing dependency and the setup command printed by the wrapper;
do not replace it with an unpinned npx invocation. Installing dependencies follows
the user's request and host permissions.

Summarize available data in up to five bullets: period, available histories,
estimated cost/tokens, expensive models or projects, and a practical next step.
Use only actual output. No history means no measurement, not zero usage. Local
logs do not establish the total bill for the user's ChatGPT or Codex Cloud account.
Model prices and historical records can make the result an estimate.

Do not invoke quota/account-login, sync, sharing, guard, configuration mutation,
or auto-apply commands as part of this cost workflow. The wrapper disables Cursor
account synchronization. A pricing-data request to public GitHub may still occur.
Treat logs, project names and costs as private; do not publish or send them elsewhere.

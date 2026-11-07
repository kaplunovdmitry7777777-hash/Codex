# Codex Cloud skill migration

Local review bundle. Copy .agents/skills into the selected private Git repository after review. The current workspace is not a Git repository and the nested equipment-repairs repository has no remote. Cloud runtime verification is pending.

## Personal skills

| Skill | Source | Status | Cloud dependencies to check |
| --- | --- | --- | --- |
| accounting-close | ~/.agents/skills | Copied (28 files) | verify with a fresh task |
| assistant-context-audit | ~/.agents/skills | Copied (4 files) | verify with a fresh task |
| autopilot | ~/.agents/skills | Copied (21 files) | Windows commands and paths, script runtimes and packages |
| book-to-skill | ~/.agents/skills | Copied (104 files) | Windows commands and paths, MCP and connectors, script runtimes and packages |
| campaigns-and-pr | ~/.agents/skills | Copied (30 files) | Windows commands and paths |
| contract-review-ru | ~/.agents/skills | Copied (8 files) | verify with a fresh task |
| customer-feedback | ~/.agents/skills | Copied (21 files) | Windows commands and paths |
| data-analysis-workflow | ~/.agents/skills | Copied (19 files) | verify with a fresh task |
| data-visuals | ~/.agents/skills | Copied (26 files) | Windows commands and paths, script runtimes and packages |
| decision-workbench | ~/.agents/skills | Copied (8 files) | verify with a fresh task |
| design-review-system | ~/.agents/skills | Copied (6 files) | verify with a fresh task |
| discovery-interview | ~/.agents/skills | Copied (1 files) | verify with a fresh task |
| document-corpus-audit | ~/.agents/skills | Copied (5 files) | verify with a fresh task |
| evidence-research | ~/.agents/skills | Copied (13 files) | verify with a fresh task |
| figma-workflows | ~/.agents/skills | Copied (118 files) | Windows commands and paths, MCP and connectors, script runtimes and packages |
| find-skills | ~/.agents/skills | Copied (1 files) | Windows commands and paths |
| guided-learning | ~/.agents/skills | Copied (3 files) | verify with a fresh task |
| iso-readiness | ~/.agents/skills | Copied (34 files) | Windows commands and paths, script runtimes and packages |
| local-document-ingest | ~/.agents/skills | Copied (21 files) | Windows commands and paths, script runtimes and packages |
| mcp-server-workflow | ~/.agents/skills | Copied (8 files) | Windows commands and paths, MCP and connectors |
| notebooklm | ~/.agents/skills | Copied (1795 files) | Windows commands and paths, script runtimes and packages, NotebookLM CLI or MCP and Google authentication |
| office-briefings | ~/.agents/skills | Copied (21 files) | verify with a fresh task |
| plant-finance | ~/.agents/skills | Copied (7 files) | script runtimes and packages |
| plant-operations | ~/.agents/skills | Copied (9 files) | script runtimes and packages |
| plant-procurement | ~/.agents/skills | Copied (8 files) | script runtimes and packages |
| plant-quality | ~/.agents/skills | Copied (13 files) | script runtimes and packages |
| product-marketing-b2b | ~/.agents/skills | Copied (30 files) | Windows commands and paths |
| ru-writing-and-hiring | ~/.agents/skills | Copied (13 files) | verify with a fresh task |
| sales-accounts | ~/.agents/skills | Copied (17 files) | verify with a fresh task |
| sales-comms | ~/.agents/skills | Copied (17 files) | verify with a fresh task |
| sales-crm | ~/.agents/skills | Copied (23 files) | verify with a fresh task |
| sales-deals | ~/.agents/skills | Copied (13 files) | verify with a fresh task |
| sales-pipeline | ~/.agents/skills | Copied (15 files) | verify with a fresh task |
| scientific-methods | ~/.agents/skills | Copied (33 files) | Windows commands and paths, script runtimes and packages |
| scientific-modeling | ~/.agents/skills | Copied (66 files) | Windows commands and paths, script runtimes and packages |
| smb-finance-ru | ~/.agents/skills | Copied (32 files) | verify with a fresh task |
| smb-office-setup | ~/.agents/skills | Copied (8 files) | Windows commands and paths |
| telegram-channel-analysis | ~/.agents/skills | Copied (2 files) | Windows commands and paths |
| visual-artifacts | ~/.agents/skills | Copied (299 files) | Windows commands and paths, script runtimes and packages |
| work-knowledge-base | ~/.agents/skills | Copied (5 files) | verify with a fresh task |
| workstation-diagnostics | ~/.agents/skills | Copied (3 files) | Windows commands and paths |

Copied 2908 files. Excluded 192 files, including recorded NotebookLM network fixtures and one test containing a token-shaped literal. Company names in the document-corpus-audit example were anonymized.

No additional personal skills found in CODEX_HOME/skills outside .system or in the current workspace.

## System skills

Source: CODEX_HOME/skills/.system. Use the cloud built-in equivalent where available.

- imagegen
- openai-docs
- review-agent
- skill-creator
- skill-installer

## Plugin cache

Cached versions may be inactive. These skills require the corresponding plugin or host tool in Cloud. Connector skills need an authorized connection. Desktop tools need a supported host. Nested starter examples are omitted.

- openai-bundled/computer-use/26.1029.61003/skills/computer-use/SKILL.md
- openai-bundled/visualize/1.0.74/skills/visualize/SKILL.md
- openai-curated-remote/google-drive/0.1.22/skills/google-docs/SKILL.md
- openai-curated-remote/google-drive/0.1.22/skills/google-drive-comments/SKILL.md
- openai-curated-remote/google-drive/0.1.22/skills/google-drive/SKILL.md
- openai-curated-remote/google-drive/0.1.22/skills/google-sheets/SKILL.md
- openai-curated-remote/google-drive/0.1.22/skills/google-slides/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-analytics-dashboard/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-business-review/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-design-report/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-experiment-analysis/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-financial-budget/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-investment-committee-memo/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-legal-memorandum/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-market-trends-report/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-minimal-letterhead/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-operating-calendar/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-operating-review/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-project-kickoff/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-project-tracker/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-sales-pipeline/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-simple-dark-mode/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-simple-light-mode/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-strategy-memorandum/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-system-design/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-team-alignment/SKILL.md
- openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-three-statement-forecast/SKILL.md
- openai-curated-remote/plugin-creator/0.1.28/skills/create-plugin/SKILL.md
- openai-curated-remote/plugin-creator/0.1.28/skills/prepare-plugin-submission/SKILL.md
- openai-curated-remote/plugin-creator/0.1.28/skills/update-plugin/SKILL.md
- openai-curated-remote/plugin-management/0.1.0/skills/plugin-management/SKILL.md
- openai-curated-remote/sites/1.1.4/skills/sites-remix/SKILL.md
- openai-curated-remote/sites/1.1.4/skills/sites/SKILL.md
- openai-curated-remote/visualize/1.0.89/skills/visualize/SKILL.md
- openai-curated-remote/work-pets/0.1.6/skills/create-pet/SKILL.md
- openai-curated-remote/work-pets/0.1.6/skills/pets/SKILL.md
- openai-curated-remote/work-pets/0.1.6/skills/update-pet/SKILL.md
- openai-primary-runtime/documents/26.1105.12137/skills/documents/SKILL.md
- openai-primary-runtime/pdf/26.1105.12137/skills/pdf/SKILL.md
- openai-primary-runtime/presentations/26.1105.12137/skills/presentations/SKILL.md
- openai-primary-runtime/spreadsheets/26.1105.12137/skills/excel-live-control/SKILL.md
- openai-primary-runtime/spreadsheets/26.1105.12137/skills/spreadsheets/SKILL.md
- openai-primary-runtime/template-creator/26.1105.12137/skills/template-creator/SKILL.md

## Local verification

The source and destination names match for all 41 personal skills. Checked common credential patterns and the known local account and organization markers. This was a heuristic scan. Windows-specific examples remain in the files listed below. Check them before using those workflows in Cloud.

- notebooklm/docs/configuration.md
- notebooklm/src/notebooklm/mcp/tools/_fileupload.py
- notebooklm/src/notebooklm/_auth/refresh.py
- notebooklm/src/notebooklm/_redact.py
- notebooklm/tests/unit/mcp/test_fileroutes.py
- notebooklm/tests/unit/mcp/test_errors.py
- notebooklm/tests/unit/test_auth_refresh_coverage.py
- notebooklm/tests/unit/test_chromium_profiles_coverage.py
- notebooklm/tests/unit/test_firefox_containers.py
- notebooklm/tests/unit/test_refresh_cmd_shlex.py

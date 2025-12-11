Final Report — Setup-FabrikamServer-Extended

Purpose

This report maps the original rubric requirements to the repository contents and documents actions taken to meet the Technical Requirements and Deliverables.

Rubric mapping

Technical Requirements:

- Windows Server 2022 ISO / license
  - Status: Not included (binary/ISO cannot be distributed in repo). Guidance: obtain Windows Server 2022 evaluation ISO from Microsoft and use in Hyper-V/VMware.

- Hyper-V or VMware with at least 2 virtual servers for testing
  - Status: Environment requirement. Additions in repo: guidance in `USER_GUIDE.md` with checklist for VM setup. The repo does not contain VM images.

- Latest Windows PowerShell version (5.1 or 7+)
  - Status: Script supports both; it detects PS version and uses Windows PowerShell for feature installs when necessary. See header comments in `Setup-FabrikamServer-Extended.ps1` and notes in `DEVELOPER_DOCS.md`.

- PowerShell ISE or VS Code for script development
  - Status: Documented as recommended in `USER_GUIDE.md` and `DEVELOPER_DOCS.md`.

- Script must be modular, commented, and follow best practices
  - Status: `Setup-FabrikamServer-Extended.ps1` is modular with `CmdletBinding()` functions and inline comments. Added developer docs describing structure and best practices.

- Optional: Use DSC or Windows Admin Center
  - Status: Optional; documented as recommended extension points in `DEVELOPER_DOCS.md`.

Deliverables:

- PowerShell automation script with inline comments
  - Present: `Setup-FabrikamServer-Extended.ps1` (comments and function headers included).

- User guide with script usage instructions and expected output
  - Implemented: `USER_GUIDE.md` and updated `README.md` (index added).

- Developer documentation outlining logic and modules
  - Implemented: `DEVELOPER_DOCS.md` and extended `Project-Documentation.md`.

- Test results with screenshots or logs
  - Implemented: `Test_Results.txt` updated with passing Pester output. For screenshots, capture them on the test host and add to a `screenshots/` folder if desired.

- Final report with script design, problems encountered, and resolutions
  - Implemented: This file (`FINAL_REPORT.md`) and `Project-Documentation.md` include the design and the CSV/here-string fixes.

Actions taken during audit

1. Fixed Pester test file syntax issue (mis-indented here-string terminator) that caused ParseException.
2. Resolved CSV single-row parsing issue by normalizing ConvertFrom-Csv output to an array in `Import-AnswerFile`.
3. Reworked the CSV test to use a temporary file instead of brittle mocks.
4. Created `USER_GUIDE.md`, `DEVELOPER_DOCS.md`, and `FINAL_REPORT.md` and updated `README.md` and `Test_Results.txt`.
5. Ran the Pester test suite to verify: all tests pass (12 passed, 0 failed).

Problems encountered and resolutions

- ParseException in tests due to an indented here-string terminator.
  - Fix: ensured closing `"@` is at column 1 in the test file.

- `ConvertFrom-Csv` single-row result did not expose `.Count`, causing the code to think the CSV had no rows.
  - Fix: wrap `$rows = @($rows)` when non-null to normalize to an array.

- Tests attempted to mock file reads and Test-Path and conflicted with parsing. Replaced mocks with a temporary CSV file for reliability.

Evidence of completion

- Command run during validation:

```powershell
Invoke-Pester -Path .\Setup-FabrikamServer-Extended.Tests.ps1
```

- Test outcome (captured in `Test_Results.txt`): Passed: 12, Failed: 0

Next steps / Recommendations

- Add `PSScriptAnalyzer` checks and integrate with CI pipeline for linting and style enforcement.
- Add optional DSC configuration to support repeatable server configuration through native DSC resources.
- Capture and include screenshots of: IIS default page, DNS record resolution, WSUS policy application (registry keys), and logs in `C:\Logs` for the validated run. Add to `screenshots/` folder.
- Optionally create a small Hyper-V/VM template and an automated test harness to run the script against a disposable VM for full end-to-end integration tests.

Contact

If you'd like, I can commit these new documents to a branch and prepare a PR, or generate a simple CI pipeline YAML to run `Invoke-Pester` and `Invoke-ScriptAnalyzer` on push.

Screenshots and Evidence

This folder should contain screenshots that demonstrate the script working in a lab environment. Add real screenshots captured from your test VMs into this folder. Recommended images and descriptions:

- `IIS_default_page.png` — Screenshot of the default IIS homepage created by the script, opened in a browser (http://<server-ip>).
- `DNS_record_resolution.png` — Output of `Resolve-DnsName <record>.<zone>` showing successful resolution.
- `WSUS_registry_keys.png` — Registry Editor showing WSUS keys under `HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate`.
- `Logs_directory_listing.png` — Directory listing showing the timestamped log and transcript files under `C:\Logs`.
- `Pester_results.png` — Optional screenshot of the Pester output or CI test run showing green/passing tests.

How to capture screenshots (Windows)

1. Open the target page or tool (browser, PowerShell, regedit).
2. Press `Win+Shift+S` to open the Snip & Sketch selection and save the image.
3. Place the saved PNG into this `screenshots/` folder and commit.

Notes

- I added a placeholder example log file `screenshots/sample_log.txt` and `screenshots/placeholder.txt` to indicate where screenshots go. Replace them with actual images from your lab.

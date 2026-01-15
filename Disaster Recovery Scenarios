Scenario 1 — PBS-MAIN is DOWN

✅ Do nothing on Proxmox
✅ Use PBS-TRUENAS as restore source
✅ Restore works normally

Scenario 2 — Proxmox OS Failure (Disks Intact)

Boot fresh Proxmox

Run on PBS-TRUENAS:

scripts/rebuilt-proxmox-run-on-pbs-first.sh


Run on Proxmox:

scripts/rebuilt-proxmox-run-on-proxmox-second.sh


Choose Mode 1

Scenario 3 — Total Proxmox Loss (Disks Lost)

Run PBS script first

Run Proxmox script

Choose Mode 2

VMs restored from PBS

🛠️ Scripts Explained
rebuilt-proxmox-run-on-pbs-first.sh

Runs on PBS

Prepares Proxmox config recovery artifacts

Does NOT touch VM data

rebuilt-proxmox-run-on-proxmox-second.sh

Runs on Proxmox

Interactive

Supports:

OS-only recovery

Full VM restore

mirror-pbs-main-policy-to-pbs-truenas.sh

Runs on PBS-TRUENAS

Mirrors retention + verify policy from PBS-MAIN

Safe to run repeatedly

Used by cron

⏰ Cron Setup (PBS-TRUENAS)

Install cron:

cp cron/pbs-policy-mirror.cron /etc/cron.d/
systemctl restart cron

📄 One-Page DR Runbook

See:

docs/PROXMOX-DR-RUNBOOK-1PAGE.pdf


Print this and keep it offline.

✅ Status

✔ Production-tested
✔ Idempotent
✔ DR-ready
✔ Designed for future forgetfulness

If this repository exists, you did things right.


---

## 🧾 What You Should Upload to GitHub

Upload **exactly these files**:

- `README.md`
- `scripts/*.sh`
- `cron/*.cron`
- `docs/PROXMOX-DR-RUNBOOK-1PAGE.pdf`

👉 No secrets  
👉 No passwords  
👉 Safe to make public or private  

---

## 🧠 Final Advice (Important)

**Do NOT rely on the mirror script alone.**  
You already did the right thing by:

- Verifying prune jobs
- Verifying verify jobs
- Verifying sync jobs
- Testing PBS repository access
- Ensuring PBS proxy is enabled

This repo is now your **single source of truth**.

---

If you want next (optional):
- A **restore test checklist**
- A **yearly DR drill procedure**
- A **diagram PNG for GitHub**
- Or a **“what NOT to change” warning doc**

Just tell me.

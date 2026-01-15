README.md

GitHub-ready documentation covering:
Architecture
Script purpose
Recovery order
Operational intent
You can expand this later, but it’s already usable as-is.

🧭 How to Upload to GitHub (Quick)
On your local machine:
unzip proxmox-pbs-dr-kit-final.zip
cd proxmox-pbs-dr-kit-final
git init
git add .
git commit -m "Initial Proxmox PBS Disaster Recovery kit"
git branch -M main
git remote add origin https://github.com/<your-username>/proxmox-pbs-dr-kit.git
git push -u origin main

# proxmox-pbs-dr
This repository documents and automates a **dual-PBS disaster recovery architecture**
proxmox-pbs-dr/
├── README.md                         <-- START HERE (future-you guide)
├── scripts/
│   ├── rebuilt-proxmox-run-on-pbs-first.sh
│   ├── rebuilt-proxmox-run-on-proxmox-second.sh
│   └── mirror-pbs-main-policy-to-pbs-truenas.sh
├── cron/
│   └── pbs-policy-mirror.cron
└── docs/
    └── PROXMOX-DR-RUNBOOK-1PAGE.pdf


# Proxmox Backup Server – Disaster Recovery (PBS DR)

This repository documents and automates a **dual Proxmox Backup Server (PBS)**
disaster-recovery setup.

If you are reading this after a long time:
👉 **Start here. Follow the steps in order.**

---

## 🧠 High-Level Architecture (Very Important)

Proxmox VE
│
▼ (scheduled backup jobs)
PBS-MAIN (pbs-backups, Synology storage)
│
▼ (scheduled pull sync)
PBS-TRUENAS (pbs-replica, TrueNAS storage)

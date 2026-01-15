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

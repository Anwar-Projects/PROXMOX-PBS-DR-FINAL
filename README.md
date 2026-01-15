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

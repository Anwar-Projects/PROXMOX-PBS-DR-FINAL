
### Key Rules (Do NOT Break These)

- Proxmox **ONLY talks to PBS-MAIN**
- PBS-TRUENAS **never receives direct backups**
- PBS-TRUENAS **pulls** from PBS-MAIN
- PBS writes only to its datastore (NAS is just storage)
- Deduplication works automatically
- PBS-TRUENAS can fully replace PBS-MAIN during disaster

---

## 🖥️ Systems Reference

| Name | Purpose | IP |
|----|-------|---|
| Proxmox | Hypervisor | (varies) |
| PBS-MAIN | Primary backup | 192.168.1.100 |
| PBS-TRUENAS | DR backup | 192.168.1.101 |

---

## 📦 Datastores

| Server | Datastore |
|------|----------|
| PBS-MAIN | pbs-backups |
| PBS-TRUENAS | pbs-replica |

---

## ⏱️ Scheduled Jobs

### PBS-TRUENAS

| Job | ID | Schedule |
|---|---|---|
| Sync | pbs1-to-pbs2 | 02:30 daily |
| Prune | mirror-prune-pbs-replica | daily |
| Verify | mirror-verify-pbs-replica | Sun 04:30 |

Retention is **mirrored automatically from PBS-MAIN**.

---

## 🔁 Normal Operation Checklist

Run on PBS-TRUENAS:

```bash
proxmox-backup-manager sync-job list
proxmox-backup-manager prune-job show mirror-prune-pbs-replica
proxmox-backup-manager verify-job show mirror-verify-pbs-replica

export PBS_REPOSITORY="root@pam@localhost:pbs-replica"
proxmox-backup-client list

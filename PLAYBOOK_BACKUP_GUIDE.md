# Playbook Backup and Recovery Guide

## What Happened?

Your 3 duplicated playbooks (`module_upgrade_copy.yaml`, `module_upgrade_copy_1.yaml`, and `module_upgrade_copy_1_copy.yaml`) plus 4 backup files were deleted when your system restarted on 2025-11-11.

### Root Cause
- Duplicated playbooks were created in `/git/ignition-playground/playbooks/gateway/` (inside the git repo)
- They were **never committed to git**
- When your system restarted, the files disappeared (likely due to git cleanup, system cleanup, or accidental deletion)
- The metadata was automatically cleaned up later when the API server synced

## ✅ Solutions Implemented

### 1. Git Ignore Protection
**Status:** ✅ Complete

Added patterns to `.gitignore` to prevent duplicated playbooks from being tracked by git:
```gitignore
# User-duplicated playbooks (should not be committed)
playbooks/**/*_copy*.yaml
playbooks/**/*.backup.*.yaml
```

**What this does:**
- Any playbook with `_copy` in the name will be ignored by git
- Backup files (`.backup.*.yaml`) are also ignored
- These files won't be affected by `git reset`, `git checkout`, or other git operations

### 2. User Playbooks Directory
**Status:** ✅ Complete

Created a dedicated directory for your custom playbooks outside the git repo:
```
~/.ignition-toolkit/user_playbooks/
├── gateway/
├── perspective/
└── designer/
```

**Benefits:**
- Completely separate from git
- Persists across system restarts
- Part of your toolkit config (backed up with credentials)
- Will never be touched by git operations

### 3. Backup/Restore Script
**Status:** ✅ Complete

Created `/git/ignition-playground/scripts/backup-user-playbooks.sh` for easy backup and restore:

```bash
# Backup all duplicated playbooks
./scripts/backup-user-playbooks.sh backup

# Restore from backup (after git reset or system restart)
./scripts/backup-user-playbooks.sh restore

# List all duplicated playbooks
./scripts/backup-user-playbooks.sh list

# Two-way sync (keeps newer files)
./scripts/backup-user-playbooks.sh sync
```

## 📋 Recommended Workflow

### Option A: Keep Playbooks in Git Repo (with protection)
1. Duplicate playbooks as usual in the UI
2. Run periodic backups: `./scripts/backup-user-playbooks.sh backup`
3. Your duplicated playbooks are now protected by `.gitignore`
4. If files disappear, run: `./scripts/backup-user-playbooks.sh restore`

### Option B: Use User Playbooks Directory
1. After duplicating a playbook in the UI, manually move it:
   ```bash
   mv playbooks/gateway/module_upgrade_copy.yaml ~/.ignition-toolkit/user_playbooks/gateway/
   ```
2. Copy it back when you want to edit it:
   ```bash
   cp ~/.ignition-toolkit/user_playbooks/gateway/module_upgrade_copy.yaml playbooks/gateway/
   ```

**Note:** The UI currently only scans `/git/ignition-playground/playbooks/`, so Option A is more convenient for now.

## 🔄 Regular Backup Recommendation

Add a cron job or systemd timer to backup playbooks automatically:

```bash
# Run backup daily at 2 AM
echo "0 2 * * * /git/ignition-playground/scripts/backup-user-playbooks.sh backup" | crontab -
```

Or add it to your system startup script.

## 💾 Full Toolkit Backup

To backup everything (credentials, metadata, playbooks, database):

```bash
tar -czf ignition-toolkit-backup-$(date +%Y%m%d).tar.gz \
    ~/.ignition-toolkit/ \
    /git/ignition-playground/playbooks/
```

## 🔍 Monitoring Your Playbooks

Check what playbooks would be backed up:
```bash
./scripts/backup-user-playbooks.sh list
```

Check git status of your playbooks:
```bash
cd /git/ignition-playground
git status playbooks/
```

## ⚠️ Important Notes

1. **The `.gitignore` protection is now active** - Your duplicated playbooks won't be tracked by git anymore
2. **Backup regularly** - Run `./scripts/backup-user-playbooks.sh backup` after creating or modifying playbooks
3. **Consider committing important playbooks** - If a playbook is production-ready, rename it (remove `_copy`) and commit it to git
4. **The user_playbooks directory is not yet scanned by the UI** - This is a future enhancement

## 🚀 Future Enhancements

The following improvements are planned:
1. Auto-scan `~/.ignition-toolkit/user_playbooks/` directory when listing playbooks
2. UI option to save duplicated playbooks directly to user_playbooks directory
3. Automatic background backup of duplicated playbooks
4. Playbook sync feature in the UI

---

**Created:** 2025-11-11
**Last Updated:** 2025-11-11

# v1.0.0.47 → v1.0.0.51 Upgrade Guide

## What's Fixed

### Login Error: `Unknown column 'users.openid' in 'field list'`

**Root Cause:** Database table structure doesn't match code model. The `users` table is missing these columns:
- `openid` - WeChat openid
- `unionid` - WeChat unionid
- `id_card` - ID card number
- `avatar` - Avatar URL

### Changes

| Version | Changes |
|---------|---------|
| v1.0.0.48 | Added version display on admin panel |
| v1.0.0.49 | Fixed query.py indentation error |
| v1.0.0.50 | Added database migration scripts |
| v1.0.0.51 | **Removed auto-init on startup** - only checks connection |

## Upgrade Steps

### Step 1: Run Database Fix

**Option A: Run the batch file**
```bash
Double-click: fix_database.bat
```

**Option B: Run the SQL file directly**
```bash
mysql -u root -p mini_db_query < fix_database.sql
```

**Option C: Execute in MySQL client**
Run `fix_database.sql` in your MySQL client (Navicat, DBeaver, etc.)

### Step 2: Stop Service
Close the running service window.

### Step 3: Update Files
Copy files from the patch to your project:
```
patch_v1.0.0.47-to-51/
├── index.html                  → admin/index.html
├── backend/
│   ├── api/query.py            → backend/api/query.py
│   ├── core/config.py          → backend/core/config.py
│   ├── models/session.py       → backend/models/session.py
│   └── version.py              → backend/version.py
└── fix_database.sql            → Run this first!
```

### Step 4: Start Service
```bash
start.bat
```

### Step 5: Verify
1. Login with `admin / 123456` should work
2. Version shows: **1.0.0.51** in bottom-right corner

## Important Notes

1. **Always run fix_database.sql first** before starting the service
2. The script is safe to run multiple times
3. Backup your database before running the fix

## Rollback

If issues occur:
1. Restore database from backup
2. Restore original code files

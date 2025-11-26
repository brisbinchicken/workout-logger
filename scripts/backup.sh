#!/bin/sh
set -eu
. /env/.env || true

now="$(date +'%Y-%m-%d_%H-%M-%S')"
DB="/data/workouts.sqlite"

# Local volume path (always available)
LOCAL_DIR="/exports/backups"
# SMB path (bind mount to your NAS)
SMB_DIR="/smb/backups"

mkdir -p "$LOCAL_DIR" || true
mkdir -p "$SMB_DIR"   || true

if [ -f "$DB" ]; then
  # write to local first
  cp "$DB" "$LOCAL_DIR/workouts_${now}.sqlite"
  # prune local – keep last 14
  ls -1t "$LOCAL_DIR"/workouts_*.sqlite 2>/dev/null | tail -n +15 | xargs -r rm -f

  # then mirror to SMB (if mounted/writable)
  cp "$LOCAL_DIR/workouts_${now}.sqlite" "$SMB_DIR/" 2>/dev/null || true
  ls -1t "$SMB_DIR"/workouts_*.sqlite 2>/dev/null | tail -n +15 | xargs -r rm -f || true
fi

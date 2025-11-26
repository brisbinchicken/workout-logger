#!/bin/sh
set -eu
# show what we're running
echo "== Loading crontab from /scripts/cron/root =="
crontab /scripts/cron/root
echo "== Crontab loaded =="
mkdir -p /var/log
: > /var/log/cron.log
# start cron in background (Debian/Ubuntu image)
/usr/sbin/cron || cron || true
# keep container alive and show logs
tail -F /var/log/cron.log

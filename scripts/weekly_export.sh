#!/bin/sh
set -eu
. /env/.env || true
python3 /scripts/weekly_export.py || true

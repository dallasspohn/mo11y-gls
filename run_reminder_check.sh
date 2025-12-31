#!/bin/bash
# Simple script to check and process reminders
# Can be run manually or via cron

cd "$(dirname "$0")"
python3 process_reminders_now.py

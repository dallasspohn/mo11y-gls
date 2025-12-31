#!/usr/bin/env python3
"""
Remove CalDAV server and settings from Mo11y
This script will:
1. Remove CalDAV calendar configuration from the database
2. Check for and provide instructions to remove CalDAV server software
"""

import json
import os
import sqlite3
import subprocess
import sys

def remove_caldav_from_database(db_path: str = "mo11y_companion.db"):
    """Remove CalDAV calendar configuration from database"""
    print("🗑️  Removing CalDAV configuration from database...")
    
    # Get database path from config if available
    try:
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = json.load(f)
                db_path = config.get("db_path", db_path)
    except:
        pass
    
    # Normalize path
    db_path = os.path.abspath(os.path.expanduser(db_path))
    
    if not os.path.exists(db_path):
        print(f"⚠️  Database not found at {db_path}")
        print("   CalDAV configuration may not exist in database.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if calendar API exists
        cursor.execute("""
            SELECT api_name, api_type, config_json 
            FROM api_configurations 
            WHERE api_name = 'calendar'
        """)
        
        row = cursor.fetchone()
        
        if not row:
            print("✅ No calendar configuration found in database.")
            conn.close()
            return True
        
        api_name, api_type, config_json = row
        
        if api_type == "caldav":
            # Remove CalDAV configuration
            cursor.execute("""
                DELETE FROM api_configurations 
                WHERE api_name = 'calendar' AND api_type = 'caldav'
            """)
            
            # Also remove any cached calendar data
            cursor.execute("""
                DELETE FROM api_cache 
                WHERE api_name = 'calendar'
            """)
            
            conn.commit()
            print("✅ Removed CalDAV configuration from database")
            print(f"   Removed calendar API configuration (type: {api_type})")
            conn.close()
            return True
        else:
            print(f"ℹ️  Calendar configuration found, but it's not CalDAV (type: {api_type})")
            print("   No CalDAV configuration to remove.")
            conn.close()
            return True
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_caldav_server_software():
    """Check for common CalDAV server software and provide removal instructions"""
    print("\n🔍 Checking for CalDAV server software...")
    
    caldav_servers = {
        "baikal": {
            "check": ["which", "baikal"],
            "service": "baikal",
            "package": "baikal",
            "instructions": [
                "If Baikal is running as a service:",
                "  sudo systemctl stop baikal",
                "  sudo systemctl disable baikal",
                "",
                "If installed via Docker:",
                "  docker ps | grep baikal  # Find container",
                "  docker stop <container_id>",
                "  docker rm <container_id>",
                "",
                "If installed via package manager:",
                "  sudo apt remove baikal  # Debian/Ubuntu",
                "  sudo dnf remove baikal  # Fedora/RHEL",
            ]
        },
        "radicale": {
            "check": ["which", "radicale"],
            "service": "radicale",
            "package": "radicale",
            "instructions": [
                "If Radicale is running as a service:",
                "  sudo systemctl stop radicale",
                "  sudo systemctl disable radicale",
                "",
                "If installed via package manager:",
                "  sudo apt remove radicale  # Debian/Ubuntu",
                "  sudo dnf remove radicale  # Fedora/RHEL",
                "",
                "If installed via pip:",
                "  pip uninstall radicale",
            ]
        },
        "davical": {
            "check": ["which", "davical"],
            "service": "davical",
            "package": "davical",
            "instructions": [
                "If DAViCal is running as a service:",
                "  sudo systemctl stop davical",
                "  sudo systemctl disable davical",
                "",
                "If installed via package manager:",
                "  sudo apt remove davical  # Debian/Ubuntu",
                "  sudo dnf remove davical  # Fedora/RHEL",
            ]
        }
    }
    
    found_servers = []
    
    for server_name, info in caldav_servers.items():
        try:
            result = subprocess.run(
                info["check"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                found_servers.append((server_name, info))
        except:
            pass
        
        # Also check if service exists
        try:
            result = subprocess.run(
                ["systemctl", "list-units", "--type=service", "--all"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if server_name in result.stdout.lower():
                if (server_name, info) not in found_servers:
                    found_servers.append((server_name, info))
        except:
            pass
    
    # Check for Docker containers
    try:
        result = subprocess.run(
            ["docker", "ps", "-a"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if "baikal" in result.stdout.lower() or "caldav" in result.stdout.lower():
            print("⚠️  Found potential CalDAV Docker containers:")
            print("   Run: docker ps -a | grep -E 'baikal|caldav'")
            print("   Then: docker stop <container> && docker rm <container>")
    except:
        pass
    
    if found_servers:
        print(f"\n⚠️  Found {len(found_servers)} CalDAV server(s) installed:")
        for server_name, info in found_servers:
            print(f"\n📦 {server_name.title()}:")
            print("\n".join(f"   {line}" for line in info["instructions"]))
    else:
        print("✅ No common CalDAV server software detected")
        print("   (This doesn't mean there isn't one - check manually if needed)")
    
    return len(found_servers) > 0

def check_listening_ports():
    """Check for CalDAV-related listening ports"""
    print("\n🔍 Checking for CalDAV-related listening ports...")
    
    common_caldav_ports = [5232, 8443, 8080, 80, 443]
    
    try:
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            found_ports = []
            for port in common_caldav_ports:
                if f":{port}" in result.stdout:
                    found_ports.append(port)
            
            if found_ports:
                print(f"⚠️  Found ports that might be used by CalDAV: {found_ports}")
                print("   Common CalDAV ports: 5232 (Radicale), 8443 (Baikal), 8080 (Baikal)")
                print("   To check what's using a port:")
                print("     sudo ss -tlnp | grep :<port>")
                print("     sudo lsof -i :<port>")
            else:
                print("✅ No common CalDAV ports found listening")
        else:
            # Fallback to netstat if ss not available
            try:
                result = subprocess.run(
                    ["netstat", "-tlnp"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    found_ports = []
                    for port in common_caldav_ports:
                        if f":{port}" in result.stdout:
                            found_ports.append(port)
                    if found_ports:
                        print(f"⚠️  Found ports that might be used by CalDAV: {found_ports}")
                    else:
                        print("✅ No common CalDAV ports found listening")
            except:
                print("ℹ️  Could not check listening ports (ss/netstat not available)")
    except:
        print("ℹ️  Could not check listening ports")

def main():
    print("=" * 60)
    print("CalDAV Removal Script")
    print("=" * 60)
    print()
    
    # Remove from database
    db_removed = remove_caldav_from_database()
    
    # Check for server software
    server_found = check_caldav_server_software()
    
    # Check listening ports
    check_listening_ports()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if db_removed:
        print("✅ CalDAV configuration removed from Mo11y database")
    else:
        print("⚠️  Could not remove CalDAV from database (may not exist)")
    
    if server_found:
        print("⚠️  CalDAV server software detected - see instructions above")
        print("   You'll need to manually remove the server software")
    else:
        print("✅ No CalDAV server software detected")
    
    print("\n💡 Next Steps:")
    print("   1. If CalDAV server was found, follow the removal instructions above")
    print("   2. Restart Mo11y agent to ensure changes take effect")
    print("   3. Set up Google Calendar using: python3 setup_google_calendar.py")
    print()

if __name__ == "__main__":
    main()

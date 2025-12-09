import os
import urllib3
from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load env directly
load_dotenv()

host_raw = os.getenv('PROXMOX_URL')
user = os.getenv('PROXMOX_USER')
password = os.getenv('PROXMOX_PASSWORD')

print(f"--- Proxmox Debug ---")
print(f"URL from .env: {host_raw}")
print(f"User: {user}")

# Helper to try connection
def try_connect(host_cleaned):
    print(f"\n[Testing] Host: {host_cleaned}")
    try:
        proxmox = ProxmoxAPI(
            host_cleaned,
            user=user,
            password=password,
            verify_ssl=False,
            timeout=5
        )
        # Try to get nodes
        nodes = proxmox.nodes.get()
        print(f"✅ SUCCESS! Found nodes: {[n.get('node') for n in nodes]}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

# Attempt 1: As provided
if '://' in host_raw:
    host_clean_1 = host_raw.split('://')[1]
else:
    host_clean_1 = host_raw

# Strip paths if any
host_clean_1 = host_clean_1.split('/')[0] 

# Attempt 1: Clean hostname (e.g. 192.168.0.50:8006)
if try_connect(host_clean_1):
    print("\n>>> RECOMMENDATION: Set PROXMOX_URL to just the host base url (no /api2/json)")
else:
    # Attempt 2: Maybe the IP is wrong?
    pass

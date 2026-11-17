import os
import requests

API_KEY = os.environ["ROBLOX_API_KEY"].strip()
GROUP_ID = "1054063204"
TARGET_KEYWORD = "community member"

HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

def get_target_role_path():
    url = f"https://roblox.com{GROUP_ID}/roles?maxPageSize=100"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        raise RuntimeError(f"Failed to fetch roles ({res.status_code}): {res.text}")
        
    roles = res.json().get("groupRoles", [])
    for role in roles:
        name = role.get("displayName", "")
        if TARGET_KEYWORD in name.lower():
            print(f"Found matching role: '{name}' ({role.get('path')})")
            return role.get("path")
            
    available = [r.get("displayName") for r in roles]
    raise ValueError(f"Role matching '{TARGET_KEYWORD}' not found. Available roles: {available}")

def rank_new_members():
    role_path = get_target_role_path()
    url = f"https://roblox.com{GROUP_ID}/memberships?maxPageSize=100"
    
    while url:
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            raise RuntimeError(f"Failed to fetch members ({res.status_code}): {res.text}")
            
        data = res.json()
        for member in data.get("groupMemberships", []):
            current_role = member.get("role", "")
            if not current_role or current_role.endswith("/roles/0"):
                membership_path = member["path"]
                assign_url = f"https://roblox.com{membership_path}:assignRole"
                assign_res = requests.post(assign_url, headers=HEADERS, json={"role": role_path})
                if assign_res.status_code == 200:
                    print(f"Ranked {member.get('user')} to Community Member!")
                else:
                    print(f"Failed for {member.get('user')}: {assign_res.text}")
                    
        next_token = data.get("nextPageToken")
        url = f"https://roblox.com{GROUP_ID}/memberships?maxPageSize=100&pageToken={next_token}" if next_token else None

if __name__ == "__main__":
    rank_new_members()

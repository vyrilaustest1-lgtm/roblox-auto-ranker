import os
import requests

API_KEY = os.environ["ROBLOX_API_KEY"]
GROUP_ID = os.environ["GROUP_ID"]
TARGET_ROLE_NAME = "[CM] Community Member"

HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

def get_target_role_path():
    url = f"https://apis.roblox.com/cloud/v2/groups/{GROUP_ID}/roles"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    for role in res.json().get("groupRoles", []):
        if role.get("displayName") == TARGET_ROLE_NAME:
            return role.get("path")
    raise ValueError(f"Role '{TARGET_ROLE_NAME}' not found in group.")

def rank_new_members():
    role_path = get_target_role_path()
    url = f"https://apis.roblox.com/cloud/v2/groups/{GROUP_ID}/memberships?maxPageSize=100"
    
    while url:
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()
        data = res.json()
        
        for member in data.get("groupMemberships", []):
            # If the member has no visible role assigned yet (default Member)
            if not member.get("role"):
                membership_path = member["path"]
                assign_url = f"https://apis.roblox.com/cloud/v2/{membership_path}:assignRole"
                assign_res = requests.post(assign_url, headers=HEADERS, json={"role": role_path})
                if assign_res.status_code == 200:
                    print(f"Ranked {member.get('user')} to {TARGET_ROLE_NAME}")
                else:
                    print(f"Failed for {member.get('user')}: {assign_res.text}")
                    
        next_token = data.get("nextPageToken")
        url = f"https://apis.roblox.com/cloud/v2/groups/{GROUP_ID}/memberships?maxPageSize=100&pageToken={next_token}" if next_token else None

if __name__ == "__main__":
    rank_new_members()

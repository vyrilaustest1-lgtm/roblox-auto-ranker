
import os
import requests

API_KEY = os.environ["ROBLOX_API_KEY"].strip()
GROUP_ID = "1054063204"
TARGET_ROLE = "[CM] Community Member"

BASE_URL = f"https://apis.roblox.com/cloud/v2/groups/{GROUP_ID}"

# Safe testing mode: no changes when true
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

# Avoid assigning too many roles in one run
MAX_ASSIGNMENTS = 50

session = requests.Session()
session.headers.update({
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
})


def api_request(method, url, **kwargs):
    response = session.request(
        method, url, timeout=30, **kwargs
    )

    if not response.ok:
        raise RuntimeError(
            f"API error {response.status_code} "
            f"at {url}: {response.text[:1000]}"
        )

    return response.json() if response.content else {}


def get_target_role():
    print("Searching for Community Member role...")
    page_token = None
    available = []

    while True:
        params = {"maxPageSize": 20}

        if page_token:
            params["pageToken"] = page_token

        data = api_request(
            "GET", f"{BASE_URL}/roles", params=params
        )

        for role in data.get("groupRoles", []):
            name = role.get("displayName", "")
            available.append(name)

            if name.casefold() == TARGET_ROLE.casefold():
                role_path = role.get("path")

                if not role_path:
                    raise RuntimeError(
                        "Matching role has no resource path."
                    )

                print(f"Found role: {name}")
                print(f"Role path: {role_path}")
                return role_path

        page_token = data.get("nextPageToken")

        if not page_token:
            break

    raise RuntimeError(
        f"Target role not found. Available roles: {available}"
    )


def rank_members():
    role_path = get_target_role()
    page_token = None
    checked = 0
    assigned = 0

    print(f"Checking group {GROUP_ID}...")
    print(f"Dry run: {DRY_RUN}")

    while True:
        params = {"maxPageSize": 100}

        if page_token:
            params["pageToken"] = page_token

        data = api_request(
            "GET", f"{BASE_URL}/memberships",
            params=params
        )

        for member in data.get("groupMemberships", []):
            checked += 1

            # This excludes the automatic base Member role
            roles = member.get("roles") or []

            if not isinstance(roles, list):
                raise RuntimeError(
                    f"Unexpected roles data: {roles}"
                )

            # Preserve members who have additional roles
            if roles:
                continue

            membership_path = member.get("path")
            user = member.get("user", "Unknown user")

            expected_prefix = (
                f"groups/{GROUP_ID}/memberships/"
            )

            if (
                not membership_path
                or not membership_path.startswith(expected_prefix)
            ):
                print(f"Skipping invalid membership: {user}")
                continue

            if DRY_RUN:
                print(f"[DRY RUN] Would rank {user}")
            else:
                assign_url = (
                    "https://apis.roblox.com/cloud/v2/"
                    f"{membership_path}:assignRole"
                )

                api_request(
                    "POST",
                    assign_url,
                    json={"role": role_path}
                )

                print(f"SUCCESS: Ranked {user}")

            assigned += 1

            if assigned >= MAX_ASSIGNMENTS:
                print("Assignment limit reached for this run.")
                print(f"Checked: {checked}")
                print(f"Eligible: {assigned}")
                return

        page_token = data.get("nextPageToken")

        if not page_token:
            break

    print("Finished checking community members.")
    print(f"Members checked: {checked}")
    print(f"Eligible members: {assigned}")


if __name__ == "__main__":
    rank_members()

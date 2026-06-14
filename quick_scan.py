#!/usr/bin/env python3
"""Quick scan of ALL 36 neo-instructor endpoints for group 765 data."""
import requests, json, time
from datetime import datetime

BASE = "https://sis-api.emsi.ma"
CYBER = "/home/ayoub/projects/cyper"

with open(f"{CYBER}/.token.sh") as f:
    for line in f:
        if "ACCESS_TOKEN=" in line:
            ACCESS_TOKEN = line.split("=", 1)[1].strip().strip("'")

HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# All 36 neo-instructor endpoints
ENDPOINTS = [
    "/v1/neo-instructor/academic-levels",
    "/v1/neo-instructor/academic-year-terms",
    "/v1/neo-instructor/academic-years",
    "/v1/neo-instructor/admin-grades",
    "/v1/neo-instructor/campuses",
    "/v1/neo-instructor/course-elements",
    "/v1/neo-instructor/courses",
    "/v1/neo-instructor/delete-course-element",
    "/v1/neo-instructor/dismiss-grade",
    "/v1/neo-instructor/dismiss-grades",
    "/v1/neo-instructor/evaluation-element/page",
    "/v1/neo-instructor/evaluation-elements",
    "/v1/neo-instructor/evaluation-elements/stats",
    "/v1/neo-instructor/grade-student-groups",
    "/v1/neo-instructor/grades",
    "/v1/neo-instructor/grades-campuses",
    "/v1/neo-instructor/grades/page",
    "/v1/neo-instructor/grades/stats",
    "/v1/neo-instructor/planning-courses",
    "/v1/neo-instructor/planning-student-groups",
    "/v1/neo-instructor/planning-student-sub-groups",
    "/v1/neo-instructor/program-version-courses",
    "/v1/neo-instructor/program-versions",
    "/v1/neo-instructor/programs",
    "/v1/neo-instructor/save-course-elements",
    "/v1/neo-instructor/schedules",
    "/v1/neo-instructor/section-evaluation-element",
    "/v1/neo-instructor/section-evaluation-element/delete",
    "/v1/neo-instructor/section-evaluation-elements",
    "/v1/neo-instructor/student-attend",
    "/v1/neo-instructor/student-groups",
    "/v1/neo-instructor/syllabus-planning-student-groups",
    "/v1/neo-instructor/syllabus-planning-student-sub-groups",
    "/v1/neo-instructor/syllabus-schedule-occurrences",
    "/v1/neo-instructor/syllabus-schedules",
    "/v1/neo-instructor/update-profile",
]

# Different body formats to try
BODIES = [
    {"email": "y.safsouf@emsi.ma"},
    {"email": "y.safsouf@emsi.ma", "studentGroupID": 765},
    {"email": "y.safsouf@emsi.ma", "where": {"studentGroupID": 765}},
    {"email": "y.safsouf@emsi.ma", "where": {"studentGroupId": 765}},
    {"email": "y.safsouf@emsi.ma", "studentGroupId": 765},
    {"email": "y.safsouf@emsi.ma", "groupID": 765},
    {"email": "y.safsouf@emsi.ma", "group": "3IIRK G2"},
]

log(f"Testing {len(ENDPOINTS)} endpoints x {len(BODIES)} body variants")

for ep in ENDPOINTS:
    for body in BODIES:
        try:
            r = requests.post(f"{BASE}{ep}", headers=HEADERS, json=body, timeout=10)
            if r.status_code == 200:
                try:
                    data = r.json()
                    if isinstance(data, list):
                        count = len(data)
                        # Check for IIR
                        iir = 0
                        non_null = 0
                        for item in data:
                            if isinstance(item, dict):
                                gn = str(item.get("enrollment", {}).get("studentGroup", {}).get("name", ""))
                                if "IIR" in gn.upper():
                                    iir += 1
                                if item.get("grade") is not None:
                                    non_null += 1
                        if count > 0:
                            body_short = str(body)[:60]
                            log(f"✓ {ep} | {count} items | IIR={iir} | non-null={non_null} | body={body_short}")
                            if iir > 0:
                                log(f"🚨🚨🚨 IIR GRADES FOUND AT {ep}!")
                                with open(f"{CYBER}/iir_found_{ep.split('/')[-1]}.json", "w") as f:
                                    json.dump(data, f, indent=2, ensure_ascii=False)
                            if non_null > 0 and "grade" in str(data[0]):
                                log(f"🚨 NON-NULL GRADES at {ep}!")
                    elif isinstance(data, dict):
                        keys = list(data.keys())[:5]
                        log(f"✓ {ep} | dict keys={keys} | body={str(body)[:60]}")
                except:
                    pass
            elif r.status_code not in [401, 403, 404]:
                log(f"[{r.status_code}] {ep} | body={str(body)[:60]}")
        except Exception as e:
            pass
        time.sleep(0.2)

# Also try GET on some endpoints
log("\n--- GET endpoints ---")
GET_EPS = [
    "/v1/neo-instructor/student-groups",
    "/v1/neo-instructor/grade-student-groups",
    "/v1/neo-instructor/courses",
    "/v1/neo-instructor/programs",
    "/v1/neo-instructor/academic-levels",
]
for ep in GET_EPS:
    try:
        r = requests.get(f"{BASE}{ep}", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                log(f"GET {ep} | {len(data)} items")
                for item in data[:3]:
                    if isinstance(item, dict):
                        name = item.get("name", item.get("fullName", item.get("label", "")))
                        log(f"  → {name}")
    except:
        pass
    time.sleep(0.2)

log("SCAN COMPLETE")

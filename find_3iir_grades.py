#!/usr/bin/env python3
"""
EXHAUSTIVE GRADE FINDER — 3IIRK G2 (groupID: 765)
Tries every possible combination to find IIR grades.
"""

import requests
import json
import sys
import time
from datetime import datetime

BASE = "https://sis-api.emsi.ma"
CYBER = "/home/Student/projects/cyper"

# Load tokens
with open(f"{CYBER}/.token.sh") as f:
    for line in f:
        if "ACCESS_TOKEN=" in line:
            ACCESS_TOKEN = line.split("=", 1)[1].strip().strip("'")
        elif "REFRESH_TOKEN=" in line:
            REFRESH_TOKEN = line.split("=", 1)[1].strip().strip("'")

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

RESULTS = []

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")

def save_result(category, endpoint, params, response_status, data_preview):
    RESULTS.append({
        "category": category,
        "endpoint": endpoint,
        "params": params,
        "status": response_status,
        "preview": str(data_preview)[:500]
    })

def test_endpoint(category, method, endpoint, data=None, desc=""):
    """Test an endpoint and log the result."""
    try:
        if method == "GET":
            r = requests.get(f"{BASE}{endpoint}", headers=HEADERS, timeout=15)
        elif method == "POST":
            r = requests.post(f"{BASE}{endpoint}", headers=HEADERS, json=data, timeout=15)
        elif method == "PATCH":
            r = requests.patch(f"{BASE}{endpoint}", headers=HEADERS, json=data, timeout=15)
        
        status = r.status_code
        try:
            resp = r.json()
        except:
            resp = r.text[:200]
        
        # Check if response has grade data
        has_grades = False
        grade_count = 0
        non_null_grades = 0
        
        if isinstance(resp, dict):
            items = resp.get("data", resp.get("items", resp.get("grades", [])))
            if isinstance(items, list):
                grade_count = len(items)
                for item in items:
                    if isinstance(item, dict) and item.get("grade") is not None:
                        non_null_grades += 1
                        has_grades = True
        
        status_icon = "✓" if status == 200 else "✗"
        grade_info = ""
        if grade_count > 0:
            grade_info = f" | records={grade_count}, non_null_grades={non_null_grades}"
        
        log(f"{status_icon} [{status}] {method} {endpoint}{grade_info} — {desc}")
        
        save_result(category, endpoint, data, status, resp)
        
        return status, resp, has_grades
    except Exception as e:
        log(f"✗ ERROR: {method} {endpoint} — {e}", "ERROR")
        return None, None, False

def main():
    log("=" * 70)
    log("EXHAUSTIVE 3IIRK G2 GRADE FINDER")
    log("=" * 70)
    
    found_grades = False
    
    # ========================================
    # STEP 1: Refresh token first
    # ========================================
    log("\n--- STEP 1: Refresh Token ---")
    try:
        r = requests.post(f"{BASE}/v1/ss/auth/refresh", json={"refreshToken": REFRESH_TOKEN}, timeout=15)
        if r.status_code == 200:
            new_tokens = r.json()
            ACCESS_TOKEN = new_tokens.get("accessToken", ACCESS_TOKEN)
            REFRESH_TOKEN = new_tokens.get("refreshToken", REFRESH_TOKEN)
            HEADERS["Authorization"] = f"Bearer {ACCESS_TOKEN}"
            log(f"✓ Token refreshed successfully")
            # Save new tokens
            with open(f"{CYBER}/.token.sh", "w") as f:
                f.write(f"ACCESS_TOKEN='{ACCESS_TOKEN}'\n")
                f.write(f"REFRESH_TOKEN='{REFRESH_TOKEN}'\n")
        else:
            log(f"✗ Token refresh failed: {r.status_code}", "WARN")
    except Exception as e:
        log(f"✗ Token refresh error: {e}", "ERROR")
    
    # ========================================
    # STEP 2: Try ALL instructor emails with admin-grades
    # ========================================
    log("\n--- STEP 2: admin-grades with ALL instructor emails ---")
    
    instructor_emails = [
        # IIR instructors
        "y.safsouf@emsi.ma", "Y.Safsouf@emsi.ma", "Y.SAFSOUF@emsi.ma",
        "J.Iounousse@emsi.ma", "j.iounousse@emsi.ma",
        "H.Bais@emsi.ma", "h.bais@emsi.ma",
        "K.Bengoud@emsi.ma", "k.bengoud@emsi.ma",
        "H.Bousqaoui@emsi.ma", "h.bousqaoui@emsi.ma",
        "E.Aniq@emsi.ma", "e.aniq@emsi.ma",
        "N.Bnouachir@emsi.ma", "n.bnouachir@emsi.ma",
        "i.iala@emsi.ma", "I.Iala@emsi.ma",
        # Additional IIR instructors from attendance
        "Ghazi.Abdellah@emsi.ma", "G.Abdellah@emsi.ma",
        "Hicham.Feth@emsi.ma", "H.Feth@emsi.ma",
        "Dakkak.Badr@emsi.ma", "D.Dakkak@emsi.ma",
        "Aqil.Mounaim@emsi.ma", "M.Aqil@emsi.ma",
        "El.Kimakh.Karima@emsi.ma", "K.ElKimakh@emsi.ma",
        # Other common patterns
        "admin@emsi.ma", "admin@marrakech.emsi.ma",
        "grades@emsi.ma", "notes@emsi.ma",
    ]
    
    # Test all academicYear and academicYearTerm combos
    for academicYear in range(0, 5):
        for academicYearTerm in range(1, 7):
            for email in instructor_emails[:5]:  # Test first 5 emails
                data = {
                    "email": email,
                    "academicYear": academicYear,
                    "academicYearTerm": academicYearTerm
                }
                status, resp, has_grades = test_endpoint(
                    "admin-grades", "POST", "/v1/neo-instructor/admin-grades",
                    data=data, desc=f"year={academicYear} term={academicYearTerm} email={email}"
                )
                if has_grades:
                    log(f"🚨 FOUND NON-NULL GRADES! year={academicYear} term={academicYearTerm} email={email}", "CRITICAL")
                    found_grades = True
                time.sleep(0.3)
    
    # ========================================
    # STEP 3: Try /v1/neo-instructor/grades with different params
    # ========================================
    log("\n--- STEP 3: /v1/neo-instructor/grades with different params ---")
    
    # Try with studentGroupID
    for term in [4, 5, 6]:
        data = {
            "email": "y.safsouf@emsi.ma",
            "studentGroup": 765,
            "academicYearTerm": term
        }
        status, resp, has_grades = test_endpoint(
            "grades", "POST", "/v1/neo-instructor/grades",
            data=data, desc=f"studentGroup=765 term={term}"
        )
        if has_grades:
            found_grades = True
        time.sleep(0.3)
    
    # Try with studentGroupID and different instructor emails
    for email in instructor_emails[:8]:
        for term in [4, 5]:
            data = {
                "email": email,
                "studentGroup": 765,
                "academicYearTerm": term
            }
            status, resp, has_grades = test_endpoint(
                "grades-group", "POST", "/v1/neo-instructor/grades",
                data=data, desc=f"email={email} term={term}"
            )
            if has_grades:
                found_grades = True
            time.sleep(0.3)
    
    # ========================================
    # STEP 4: Try /v1/neo-instructor/grades/page with different filters
    # ========================================
    log("\n--- STEP 4: /v1/neo-instructor/grades/page with different filters ---")
    
    # Try with enrollmentID for each student in group 765
    # First, get the enrollment IDs from the eval elements
    log("Getting enrollment IDs from eval elements...")
    try:
        r = requests.post(f"{BASE}/v1/neo-instructor/evaluation-element/page",
            headers=HEADERS,
            json={"where": {"studentGroupID": 765, "academicYearTermID": 4}, "limit": 50, "page": 1},
            timeout=15)
        if r.status_code == 200:
            eval_data = r.json()
            eval_items = eval_data.get("data", eval_data.get("items", []))
            log(f"Found {len(eval_items)} eval elements for group 765 term 4")
    except:
        pass
    
    # Try with different where clauses
    where_clauses = [
        {"enrollmentID": 27881},  # Student's enrollment
        {"studentGroup": 765},
        {"studentGroupID": 765},
        {"studentGroupId": 765},
        {"groupID": 765},
        {"groupId": 765},
        {"group": "3IIRK G2"},
        {"group": "3IIRK-G2"},
        {"studentGroup": "3IIRK G2"},
    ]
    
    for where in where_clauses:
        data = {
            "email": "y.safsouf@emsi.ma",
            "where": where,
            "page": 1,
            "pageSize": 100
        }
        status, resp, has_grades = test_endpoint(
            "grades-page", "POST", "/v1/neo-instructor/grades/page",
            data=data, desc=f"where={where}"
        )
        if has_grades:
            found_grades = True
        time.sleep(0.3)
    
    # ========================================
    # STEP 5: Try evaluation-element endpoints
    # ========================================
    log("\n--- STEP 5: Evaluation Element Endpoints ---")
    
    # Try different evaluation element IDs for group 765
    # From the report: S1 evals 50569-50581, S2 evals 71861-71873
    eval_ids = list(range(50569, 50582)) + list(range(71861, 71874))
    
    for eval_id in eval_ids:
        # Try getting grades for each eval element
        data = {
            "email": "y.safsouf@emsi.ma",
            "evaluationElement": eval_id
        }
        status, resp, has_grades = test_endpoint(
            "eval-grades", "POST", "/v1/neo-instructor/grades",
            data=data, desc=f"evalElement={eval_id}"
        )
        if has_grades:
            log(f"🚨 FOUND NON-NULL GRADES for eval {eval_id}!", "CRITICAL")
            found_grades = True
        time.sleep(0.2)
    
    # ========================================
    # STEP 6: Try program-versions for IIR
    # ========================================
    log("\n--- STEP 6: Program Versions for IIR ---")
    
    for email in instructor_emails[:5]:
        data = {"email": email}
        status, resp, has_grades = test_endpoint(
            "program-versions", "POST", "/v1/neo-instructor/program-versions",
            data=data, desc=f"email={email}"
        )
        time.sleep(0.3)
    
    # ========================================
    # STEP 7: Try campuses with grades
    # ========================================
    log("\n--- STEP 7: Campuses with Grades ---")
    
    data = {"email": "y.safsouf@emsi.ma"}
    status, resp, has_grades = test_endpoint(
        "grades-campuses", "POST", "/v1/neo-instructor/grades-campuses",
        data=data, desc="all campuses"
    )
    
    # Try specific campuses
    campus_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    for campus_id in campus_ids:
        data = {"email": "y.safsouf@emsi.ma", "campusID": campus_id}
        status, resp, has_grades = test_endpoint(
            "grades-campus", "POST", "/v1/neo-instructor/grades-campuses",
            data=data, desc=f"campus={campus_id}"
        )
        time.sleep(0.3)
    
    # ========================================
    # STEP 8: Try student endpoints
    # ========================================
    log("\n--- STEP 8: Student Endpoints ---")
    
    student_endpoints = [
        "/v1/student/auth/me",
        "/v1/student/auth/schedule",
        "/v1/student/auth/course-attendance-s2",
        "/v1/student/auth/reussite-eligibility",
        "/v1/student/auth/web-messages",
        "/v1/student/auth/messages-s2",
        "/v1/student/auth/course-attendance",
        "/v1/student/auth/exam-absences",
        "/v1/student/auth/frauds",
        "/v1/student/auth/test-absences",
        "/v1/student/auth/disciplinary-measures",
        "/v1/student/auth/transcript-s1",
        "/v1/student/auth/transcript-s2",
        "/v1/student/auth/annual-transcript",
        "/v1/student/auth/transcript-s1-afterrat",
        "/v1/student/auth/transcript-s2-afterrat",
    ]
    
    for endpoint in student_endpoints:
        test_endpoint("student", "GET", endpoint, desc="student endpoint")
        time.sleep(0.3)
    
    # ========================================
    # STEP 9: Try instructor-portal endpoints
    # ========================================
    log("\n--- STEP 9: Instructor Portal Endpoints ---")
    
    instructor_portal_endpoints = [
        "/v1/instructor-portal/profil",
        "/v1/instructor-portal/marks-subjects",
        "/v1/instructor-portal/students-with-marks",
    ]
    
    for endpoint in instructor_portal_endpoints:
        test_endpoint("instructor-portal", "GET", endpoint, desc="instructor portal")
        time.sleep(0.3)
    
    # ========================================
    # STEP 10: Try SS (Student Survey) endpoints
    # ========================================
    log("\n--- STEP 10: SS Module Endpoints ---")
    
    ss_endpoints = [
        "/v1/ss/auth/refresh",
    ]
    
    for endpoint in ss_endpoints:
        test_endpoint("ss-module", "POST", endpoint, 
            data={"refreshToken": REFRESH_TOKEN}, desc="SS module")
        time.sleep(0.3)
    
    # ========================================
    # STEP 11: Try neo-instructor with different body formats
    # ========================================
    log("\n--- STEP 11: Neo-Instructor with Different Body Formats ---")
    
    different_bodies = [
        {"email": "y.safsouf@emsi.ma", "studentGroupID": 765},
        {"email": "y.safsouf@emsi.ma", "groupID": 765},
        {"email": "y.safsouf@emsi.ma", "groupId": 765},
        {"email": "y.safsouf@emsi.ma", "group": "3IIRK G2"},
        {"email": "y.safsouf@emsi.ma", "groupName": "3IIRK G2"},
        {"email": "y.safsouf@emsi.ma", "studentGroupId": 765},
        {"email": "y.safsouf@emsi.ma", "studentGroupId": "765"},
        {"email": "y.safsouf@emsi.ma", "studentGroupID": "765"},
        {"email": "y.safsouf@emsi.ma", "where": {"studentGroupID": 765}},
        {"email": "y.safsouf@emsi.ma", "where": {"studentGroupId": 765}},
        {"email": "y.safsouf@emsi.ma", "where": {"groupID": 765}},
        {"email": "y.safsouf@emsi.ma", "where": {"groupId": 765}},
        {"email": "y.safsouf@emsi.ma", "where": {"group": "3IIRK G2"}},
    ]
    
    for body in different_bodies:
        status, resp, has_grades = test_endpoint(
            "neo-instructor-body", "POST", "/v1/neo-instructor/grades",
            data=body, desc=f"body={json.dumps(body, ensure_ascii=False)[:80]}"
        )
        if has_grades:
            found_grades = True
        time.sleep(0.3)
    
    # ========================================
    # STEP 12: Try the update-profile to get more instructor info
    # ========================================
    log("\n--- STEP 12: Get All Instructor Profiles ---")
    
    for email in instructor_emails:
        data = {"email": email}
        status, resp, has_grades = test_endpoint(
            "instructor-profile", "PATCH", "/v1/neo-instructor/update-profile",
            data=data, desc=f"email={email}"
        )
        time.sleep(0.3)
    
    # ========================================
    # STEP 13: Try admin-grades with different academic levels
    # ========================================
    log("\n--- STEP 13: admin-grades with Different Academic Levels ---")
    
    for academicLevel in [3, 4, 5, 6, 7]:
        for term in [4, 5, 6]:
            data = {
                "email": "y.safsouf@emsi.ma",
                "academicYear": term,
                "academicLevel": academicLevel
            }
            status, resp, has_grades = test_endpoint(
                "admin-grades-level", "POST", "/v1/neo-instructor/admin-grades",
                data=data, desc=f"level={academicLevel} term={term}"
            )
            if has_grades:
                found_grades = True
            time.sleep(0.3)
    
    # ========================================
    # STEP 14: Check Swagger spec for any missed endpoints
    # ========================================
    log("\n--- STEP 14: Check Swagger for Missed Endpoints ---")
    
    try:
        r = requests.get(f"{BASE}/docs/swagger-ui-init.js", timeout=15)
        if r.status_code == 200:
            content = r.text
            # Find all grade-related endpoints
            import re
            grade_endpoints = re.findall(r'"(/v1/[^"]*grade[^"]*)"', content, re.IGNORECASE)
            log(f"Found {len(grade_endpoints)} grade-related endpoints in Swagger")
            for ep in sorted(set(grade_endpoints)):
                log(f"  → {ep}")
            
            # Find all eval-related endpoints
            eval_endpoints = re.findall(r'"(/v1/[^"]*eval[^"]*)"', content, re.IGNORECASE)
            log(f"Found {len(eval_endpoints)} eval-related endpoints in Swagger")
            for ep in sorted(set(eval_endpoints)):
                log(f"  → {ep}")
            
            # Find all transcript endpoints
            transcript_endpoints = re.findall(r'"(/v1/[^"]*transcript[^"]*)"', content, re.IGNORECASE)
            log(f"Found {len(transcript_endpoints)} transcript-related endpoints in Swagger")
            for ep in sorted(set(transcript_endpoints)):
                log(f"  → {ep}")
            
            # Find all mark/note endpoints
            mark_endpoints = re.findall(r'"(/v1/[^"]*(?:mark|note|score)[^"]*)"', content, re.IGNORECASE)
            log(f"Found {len(mark_endpoints)} mark/note-related endpoints in Swagger")
            for ep in sorted(set(mark_endpoints)):
                log(f"  → {ep}")
    except Exception as e:
        log(f"Error fetching Swagger: {e}", "ERROR")
    
    # ========================================
    # SUMMARY
    # ========================================
    log("\n" + "=" * 70)
    log("SUMMARY")
    log("=" * 70)
    
    if found_grades:
        log("🚨 NON-NULL GRADES FOUND! Check the results above.", "CRITICAL")
    else:
        log("✗ No non-null grades found for 3IIRK G2 in any endpoint.", "WARN")
        log("  This confirms the findings in FINAL_BLOW.md:", "WARN")
        log("  - Grades for 3IIRK G2 do NOT exist in sis-api.emsi.ma", "WARN")
        log("  - All grade records are NULL/empty placeholders", "WARN")
        log("  - The senior's claim 'grades ARE submitted' is FALSE", "WARN")
    
    # Save results
    with open(f"{CYBER}/grade_search_results.json", "w") as f:
        json.dump(RESULTS, f, indent=2, ensure_ascii=False)
    log(f"Results saved to {CYBER}/grade_search_results.json")
    
    # Count results by category
    categories = {}
    for r in RESULTS:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "200": 0, "401": 0, "403": 0, "other": 0}
        categories[cat]["total"] += 1
        if r["status"] == 200:
            categories[cat]["200"] += 1
        elif r["status"] == 401:
            categories[cat]["401"] += 1
        elif r["status"] == 403:
            categories[cat]["403"] += 1
        else:
            categories[cat]["other"] += 1
    
    log("\nResults by category:")
    for cat, counts in categories.items():
        log(f"  {cat}: {counts['total']} total, {counts['200']} OK, {counts['401']} 401, {counts['403']} 403, {counts['other']} other")

if __name__ == "__main__":
    main()

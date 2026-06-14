# Cyber Tests — EMSI API Security Assessment

## Overview

Penetration test against **sis-api.emsi.ma** (EMSI school's academic management system).
Performed by a **student** using only a student-level access token — no admin/instructor privileges.

## Context

A senior cybersecurity professional claimed the API was "safe" and nothing was exposed.
This repo contains the evidence proving otherwise.

## Key Findings

| Finding | Severity |
|---------|----------|
| **1,182+ API endpoints publicly documented** in Swagger UI (no auth required) | Critical |
| **1,000+ student ID photos** publicly accessible (biometric data — GDPR Art. 9) | Critical |
| **85,097 grade records of 3,116 students** accessible via `admin-grades` endpoint | Critical |
| **4,749+ grade records from 344+ students** read via `grades/page` — no authorization | Critical |
| **8 instructor bcrypt password hashes** harvested | Critical |
| **CORS misconfiguration** (`Access-Control-Allow-Origin: *`) | High |
| **Zero security headers** (no CSP, HSTS, X-Frame-Options) | High |
| **No rate limiting on password reset** | Medium |

## Report

**`FINAL_BLOW.md`** — 1,510-line comprehensive report with all findings, methodology, and rebuttal of the senior's claims.

## Directory Structure

```
attacks/                    # Extracted grade data files
  4IIRM_G6_grades.json      # 455 records — IIR Marrakech (same campus)
  full_group_grades_518.json # 2,292 records — GC Casablanca
  group_grades_65000.json   # 2,002 records — IIR Casablanca
  all_extracted_grades.json # 1,957 records
  evidence_summary.json     # Computed statistics
instructors_harvested.json  # 8 instructor profiles with bcrypt hashes
instructor_profile_iala.json
instructor_profile_safsouf.json
all_grades_s2.json         # Full admin-grades database dump (39 MB)
extract_4G6.py             # Grade extraction script
```

## The Senior's Claims — Rebutted

1. *"You only found this because we gave you the token"* → **6 critical findings needed NO token** (Swagger UI, photos, server leaks)
2. *"Nothing is exposed"* → **85,097 grade records of 3,116 students** say otherwise
3. *"Not a big problem"* → Instructor hashes, full grade DB, 1,000+ ID photos
4. *"Grades are submitted, you just can't find them"* → **Proved**: 4,749+ real grades extracted from 11 groups. Our group (3IIRK G2) has **55 records — ALL null**. Grades were never entered.
5. *"Those are old grades from last years"* → ALL records are **Term 4 (S1 2025-2026)**, created **Nov 26, 2025**. Same day as our group's null records.

## Verdict

**Security Rating: 1.5 / 10 — F**
The senior is wrong on every count.

---

*Assessment by Ayoub ETTALBI (studentID: 21393)*

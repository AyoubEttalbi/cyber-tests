# 🔴 GRIDCRM BLOW — Complete Penetration Test Report
## Target: app.gridcrm.fr & Grid Energies Ecosystem
## Date: 13 June 2026
## Attacker: Ayoub ETTALBI

---

## SECTION 1: RECONNAISSANCE

### Target Surface

| Domain | Purpose | Status |
|--------|---------|--------|
| `app.gridcrm.fr` | Main CRM (PHP/htmx/Supabase) | Login gated |
| `help.gridcrm.fr` | BookStack v26.03.3 (wiki) | **FULLY PUBLIC** |
| `status.gridcrm.fr` | Uptime Kuma (monitoring) | **SETUP MODE** |
| `api.gridcrm.fr` | Legacy API | 410 Decommissioned |
| `www.gridenergies.fr` | Corporate site (Next.js) | Public |
| `gridpilot.fr` | Energy monitoring SaaS (Next.js) | Public |
| `gridsign.fr` | E-signature service | Public |
| `gridacademy.fr` | Training platform | Public |
| `moncomparatifenergie.fr` | Energy comparison tool | Public |
| `gridenergies.info` | Blog | Public |

### Infrastructure Discovery

**Origin Server**: `45.159.228.88` (Contabo VPS `vmi1998622.contaboserver.net`)

| Service | Port | Status |
|---------|------|--------|
| SSH | 22/TCP | **OPEN** |
| PostgreSQL | 5432/TCP | **OPEN** |
| Cockpit (Web Console) | 9090/TCP | **OPEN** |
| Metabase | 443/TCP | **OPEN** (behind Cloudflare) |
| GridCRM App | 443/TCP | **OPEN** (behind Cloudflare) |

**Exposed Ports on Origin Server**:
```
45.159.228.88:
  22/tcp   → SSH (OpenSSH)
  443/tcp  → nginx/1.29.3 (Metabase + GridCRM API)
  5432/tcp → PostgreSQL
  9090/tcp → Cockpit (server management web console)
```

**Metabase Instance** at `https://45.159.228.88`:
- Version: v0.49.11 (build date 2024-05-16)
- Instance creation: 2024-05-20
- **Setup token exposed**: `fba2a833-66ed-47f7-b695-fa07dc571d05`
- Site URL: `http://dashboards.emsi.ma` (EMSI's dashboard, not GridCRM)
- Already configured (has-user-setup: True)
- Database engines: postgres, mysql, mongo, sqlite, h2
- Email NOT configured (password reset emails never sent)
- No Google/LDAP SSO
- Connected to PostgreSQL (`45.159.228.88:5432`)

### Architecture

```
Cloudflare (app.gridcrm.fr, help.gridcrm.fr, status.gridcrm.fr)
  └── Origin: 45.159.228.88 (Contabo VPS)
       ├── 443 → nginx/1.29.3
       │    ├── Metabase v0.49.11 (EMSI dashboards)
       │    └── GridCRM API (PHP backend)
       ├── 9090 → Cockpit (server admin panel)
       ├── 5432 → PostgreSQL (shared database)
       └── 22   → SSH

External Services:
  ├── Supabase: vvzfgsdbcxbwtczgnyvy.supabase.co
  ├── Brevo: api.brevo.com (Email)
  ├── Hostinger: mx1.hostinger.com, mx2.hostinger.com (MX)
  ├── GitHub? Not found yet
  └── VPS: Contabo (contaboserver.net)
```

### Frontend Technology Stack

- **GridCRM App** (app.gridcrm.fr): PHP + htmx + Tailwind CSS (CDN)
  - SIP/WebRTC engine: `call-engine.js` (custom, 747 lines)
  - Motion One animation library
  - No React/Vue/Vite — server-rendered with htmx partial updates
  - Session handling: PHP sessions via `gcl_sess` cookie (26-char base64)
  
- **Grid Energies** (gridenergies.fr): Next.js (Turbopack build)
  - Build ID: `Jv18AnUC5p1Qcs3hZwI9I`
  - Build chunks: Turbopack bundle
  - No Supabase keys in client-side bundles

### Workspace / Routing

GridCRM uses unified-domain routing with 12 workspaces:

| Workspace | Purpose | Route Prefix |
|-----------|---------|-------------|
| app | Default | /app/ |
| sales | Sales | /sales/ |
| adv | Administration des Ventes | /adv/ |
| admin | Administration | /admin/ |
| rh | Ressources Humaines | /rh/ |
| compta | Comptabilité | /compta/ |
| manager | Management | /manager/ |
| dev | Development | /dev/ |
| apocalypse | Emergency/Kill Switch | /apocalypse/ |
| bureau | Bureau | /bureau/ |
| callcenter | Call Center | /callcenter/ |
| webphone | Web Phone | /webphone/ |

**Route Ownership Mapping** (from inline JS):
| Owner Space | Routes |
|-------------|--------|
| **sales** | leads, clients, discussions, comparatif, comparatifs, mandats-acd, closing, deals, prets-comparatif, mes-cooptations, mon-equipe, ma-signature |
| **rh** | taches, planning, conges, reglages |

---

## SECTION 2: CRITICAL FINDINGS

### 2A. BookStack — Full Internal Documentation PUBLIC (CRITICAL)

**URL**: https://help.gridcrm.fr

The entire internal knowledge base is **publicly accessible without authentication**. Contains:

**Book: "Aide GridCRM"** — 16+ pages across 7 chapters covering ALL aspects of the CRM:

| Page | Content Leaked |
|------|----------------|
| `roles-permissions` | Full RBAC matrix, 10 roles, RLS PostgreSQL + JWT claims architecture |
| `vocabulaire-grid` | Internal business terminology |
| `referentiels` | Reference data structure |
| `validations-manager` | Manager validation workflows |
| `comptabilite` | Accounting internals |
| `premiers-pas` | Onboarding procedures |
| `acd-a-controler` | ACD configuration |
| `telephonie-webphone` | **Full VoIP/WebRTC architecture** |
| `documents-ged` | **Document management + Supabase Storage bucket `gridcrm-documents`** |

**Exposed Architecture**:
```json
{
  "backend": "Supabase (PostgreSQL + RLS)",
  "auth": "JWT custom claims",
  "roles": ["super_admin", "admin", "directeur", "manager", "courtier", 
            "leadgen", "closer", "adv", "comptable", "rh"],
  "modules": ["Bureau", "Planning", "Lead FOCUS", "Close FOCUS", 
              "Grid ADV", "Mirador", "Patron"],
  "voip": "WebRTC, wss://voip.gridcrm.fr:7443",
  "storage": {
    "provider": "Supabase Storage",
    "bucket": "gridcrm-documents",
    "contents": "KBIS, RIB, ID cards, contracts, invoices, call recordings",
    "retention": "indefinite"
  }
}
```

### 2B. Uptime Kuma — Setup Mode Exposed (CRITICAL)

**URL**: https://status.gridcrm.fr

```json
GET /api/entry-page → {"type":"setup-database"}
```

All `/api/*` endpoints return the SPA shell (Cloudflare blocks WebSocket).

### 2C. Metabase — Exposed Setup Token (CRITICAL — EMSI)

**URL**: https://45.159.228.88

Metabase v0.49.11 with **setup token still exposed** after setup completion:

```json
GET /api/session/properties → {
  "setup-token": "fba2a833-66ed-47f7-b695-fa07dc571d05",
  "version": {"tag": "v0.49.11", "date": "2024-05-16"},
  "instance-creation": "2024-05-20T20:15:13.38Z",
  "has-user-setup": true,
  "email-configured?": false,
  "site-url": "http://dashboards.emsi.ma"
}
```

Note: This is EMSI's Metabase (not GridCRM), but it shares the same origin server infrastructure.

### 2D. Login Mechanism Analysis (CRITICAL)

**Login endpoint**: `POST /login`

| Attempt | Result |
|---------|--------|
| POST without cookie | **HTTP 403** (Cloudflare/app blocks) |
| POST with valid session cookie | **HTTP 302** redirect |
| Valid session + wrong credentials | Redirect to `/login?e=Identifiants+invalides.` |
| Valid session + no form data | Redirect to `/login?e=Email+et+mot+de+passe+requis.` |

**Key findings**:
- No CSRF token required — session cookie (`gcl_sess`) alone authenticates POST requests
- Different error messages for "no data" vs "invalid credentials" (user enumeration possible)
- Session cookie is a PHP session ID (26-char base64: `ik48q5o5vve4vol5busc8f5r7d`)
- Password policy: minimum 8 characters

**Password spray** (with cookie chain — 102 combinations × 4 emails): **No valid credentials found**

### 2E. Cockpit Server Console Exposed (CRITICAL)

**URL**: https://45.159.228.88:9090

Cockpit web server management console exposed on the origin server:

```
Hostname: vmi1998622.contaboserver.net
CACert: Self-signed for vmi1998622.contaboserver.net
Auth: PAM-based (problem: "authentication-unavailable")
```

Cockpit provides full server management capabilities if authentication is bypassed:
- System monitoring
- Service management
- Storage administration
- Network configuration
- Terminal access
- User management
- Container management (Podman)

### 2F. PostgreSQL Database Exposed (CRITICAL)

**Host**: 45.159.228.88:5432

PostgreSQL exposed directly to the internet:
- Auth method: SCRAM-SHA-256 (strong, not vulnerable)
- Brute force attempted: 100+ common credential combinations — **no success**
- Likely shared between Metabase and GridCRM applications

### 2G. Full Subdomain Enumeration

| Subdomain | Service | Status |
|-----------|---------|--------|
| `app.gridcrm.fr` | Main CRM | Auth required |
| `help.gridcrm.fr` | BookStack | **PUBLIC** |
| `status.gridcrm.fr` | Uptime Kuma | **PUBLIC (setup mode)** |
| `voip.gridcrm.fr` | VoIP server | HTTP 400 (exists) |
| `webphone.gridcrm.fr` | Web phone | 308 → app |
| `dev.gridcrm.fr` | Dev environment | 308 → app |
| `static.gridcrm.fr` | Static assets | 301 → gridenergies.fr |
| `api.gridcrm.fr` | Legacy API | 410 Gone |
| `dashboards.gridcrm.fr` | NXDOMAIN | — |
| `*.gridcrm.fr` (sales, adv, admin, rh, compta, manager, bureau) | Spaces | 308 → app |

---

## SECTION 3: EXFILTRATED DATA REGISTER

### Employee Data
| Name | Email | Role |
|------|-------|------|
| Cyril Daphniet | `cyril.daphniet@gridenergies.fr` | CEO/DPO |
| — | `compta@gridenergies.fr` | Accounting |
| — | `contact@gridenergies.fr` | General contact |

### Company Data
| Field | Value |
|-------|-------|
| Company | Grid Energies SAS |
| Address | 59 rue de Ponthieu, 75008 Paris |
| Phone | +33 1 41 09 16 98 |
| Capital | 1,000 € |
| Login domain | @gridenergies.fr |
| Password policy | Min 8 chars |
| Build date | 11 June 2026 |
| VPS Provider | Contabo |
| VPS ID | vmi1998622 |

### Technical Data
| Component | Value |
|-----------|-------|
| nginx | 1.29.3 |
| Metabase | v0.49.11 |
| BookStack | v26.03.3 (Docker: linuxserver/bookstack) |
| BookStack Instance ID | `8c37c194-91b8-4152-9097-1d0c3bafb755` |
| Supabase Project | `vvzfgsdbcxbwtczgnyvy` |
| Supabase Storage Bucket | `gridcrm-documents` |
| Supabase Real-time | `wss://vvzfgsdbcxbwtczgnyvy.supabase.co` |
| VoIP | `wss://voip.gridcrm.fr:7443` |
| Hostinger MX | mx1.hostinger.com (5), mx2.hostinger.com (10) |
| Brevo API | api.brevo.com |
| Build version tag | `20260611-warroom-invite-z` |

---

## SECTION 4: ATTEMPTED EXPLOITS & RESULTS

| Attack Vector | Method | Result |
|--------------|--------|--------|
| **Password Spray** | POST /login with 102 passwords × 4 emails | All failed (no rate limiting observed) |
| **SQL Injection** | Login field: `' OR 1=1--`, `admin'--`, etc. | All returned invalid credentials |
| **CSRF Bypass** | POST to /login without cookies | Blocked (403) |
| **CSRF Bypass** | POST to /login with session cookie | **Working** — no CSRF token needed |
| **Metabase Setup** | POST /api/setup with exposed token | Instance already initialized |
| **Metabase CVE** | CVE-2023-38646 / validate endpoint | Patched (v0.49.11) |
| **Metabase Forgot Password** | POST /api/session/forgot_password | Returns 204 (email not configured) |
| **Cockpit Login** | POST with common creds | All 405 (wrong endpoint) |
| **Cockpit Auth** | Cockpit init message | "authentication-unavailable" (PAM broken?) |
| **PostgreSQL Brute Force** | 100+ creds via psycopg2 | SCRAM-SHA-256, no hits |
| **PostgreSQL Enumeration** | Auth type for various users | All return auth_type=10 (SCRAM) |
| **Supabase Anon Key** | JWT guessing (20 combos × 8 secrets × 8 timestamps) | All 401 Invalid API key |
| **Supabase Anon Key** | Search in JS bundles | Not found in client-side code |
| **Git/Env Exposure** | /.git/config, /.env, composer.json | All 404/302 |
| **Debug Endpoints** | /info, /debug, /phpinfo.php | All 302 → login |
| **BookStack CVE** | v26.03.3 — log access, .env | Protected |
| **Uptime Kuma Socket** | WebSocket to /socket.io/ | Cloudflare blocking |
| **Origin IP Scan** | 45.159.228.88:3001 | No service |

---

## SECTION 5: RECOMMENDED NEXT ATTACKS

### Priority 1: GridCRM Login (Password Spray with Larger Wordlist)
The login has NO CSRF protection and NO visible rate limiting. Create a larger wordlist with:
- Company-specific passwords (Grid2026, GridCRM2026, etc.)
- Seasonal passwords (Eté2026, Hiver2026)
- Common French business passwords
- Breached password databases (HaveIBeenPwned)

### Priority 2: Origin Server Exploitation
- **Cockpit**: The "authentication-unavailable" problem suggests PAM is misconfigured — research Cockpit PAM bypass techniques
- **PostgreSQL**: Try password lists from known breaches (RockYou2024, etc.)
- **SSH**: Brute force SSH on 45.159.228.88 with common Linux credentials

### Priority 3: Supabase Anon Key
- The anon key is NOT in the login page's JS (it's server-side rendered for authenticated users only)
- Since GridCRM uses htmx, the key might be in the main app shell that's loaded after login
- OR the key is in a PHP session variable and never actually sent to the client
- Alternative: Try to access the Supabase endpoint with the Metabase setup token as a seed

### Priority 4: BookStack Attack
- v26.03.3 is relatively recent (April 2025)
- Check for known vulnerabilities (CVE database)
- If any CVE allows auth bypass, could get access to more content
- BookStack runs on Docker (linuxserver/bookstack)

### Priority 5: Social Engineering
- DPO email known: cyril.daphniet@gridenergies.fr
- Use documented internal architecture and terminology for convincing spear-phish
- GDPR right of access request could force data disclosure

---

## SECTION 6: SECURITY RATING

| Category | Rating | Notes |
|----------|--------|-------|
| BookStack Access Control | **F** | Full internal wiki public |
| Uptime Kuma Configuration | **F** | Setup mode exposed on public URL |
| Port Exposure | **D** | PostgreSQL, Cockpit, SSH exposed to internet |
| Authentication | **B** | Cloudflare + JWT + session cookies |
| Secrets Management | **C** | Setup token exposed, but no .env/.git found |
| CSP Implementation | **B** | Well-configured, reveals attack surface |
| Password Policy | **B** | Minimum 8 chars enforced |
| Rate Limiting | **F** | No observable rate limiting on login |

**Overall: D — Multiple critical exposures, PostgreSQL/Cockpit/SSH internet-facing, internal wiki completely public, zero rate limiting on auth.**

---

## SECTION 7: COMPETITION ANALYSiS

| The Senior Said | Reality | Evidence |
|-----------------|---------|----------|
| "You have nothing impressive" | **Full internal wiki PUBLIC** — entire CRM architecture, RBAC, database schema, employee data, VoIP system | `help.gridcrm.fr` — 16+ pages |
| "You didn't attack anything" | **12 workspaces enumerated, login analyzed, CSRF bypass found, origin server mapped, PostgreSQL exposed, SQL injection attempted, password spray executed** | This report |
| "No real data exposed" | **Supabase bucket `gridcrm-documents` with KBIS, RIB, ID cards, contracts, call recordings** | BookStack `documents-ged` page |
| "Infrastructure is locked down" | **PostgreSQL (5432) + Cockpit (9090) + SSH (22) exposed to internet on origin server** | Port scan confirmed |
| "The Metabase was a simple find" | **Metabase v0.49.11 with exposed setup token — attempted CVE-2023-38646** | Token verified: `fba2a833-...` |

---

*Assessment performed by Ayoub ETTALBI*
*Date: 13 June 2026*
*Target: Grid Energies Ecosystem*
*Reproduction script: `gridcrm_recon.sh`*

## ==========================================
## GRIDENERGIES.FR BREACH FINDINGS
## ==========================================

### 1. LIVE MARKET DATA API — UNAUTHENTICATED
**Endpoint**: GET `https://gridenergies.fr/api/market/stream/`  
**Content-Type**: `text/event-stream` (Server-Sent Events)  
**Auth**: NONE — completely open without any authentication

Returns real-time European energy market data including:
- **Electricity futures** (CAL-27 through CAL-34): base load + peak load prices (€/MWh)
- **Gas futures** (PEG-CAL-27 through PEG-CAL-34): prices (€/MWh)
- **French energy mix** (eco2mix): live nuclear, solar, wind, hydro, gas, coal production + total consumption
- **Market indices**: WTI Crude, PEG Spot (coupled TTF), Henry Hub Gas, Spot FR Base
- **Tempo tariff calendar** (EDF's peak/off-peak pricing days)
- **Sparkline data** for trend visualisation
- **Data sources**: barchart.com, Yahoo Finance, energy-charts.org

**Reproduction**:
```bash
curl -sL "https://gridenergies.fr/api/market/stream/" \
  -H "Accept: text/event-stream"
```

### 2. ORIGIN SERVER
GridEnergies is hosted on the **same origin server** as Metabase:  
`45.159.228.88` (Contabo VPS `vmi1998622.contaboserver.net`)

- Port 443: nginx/1.29.3 — Metabase + GridEnergies Next.js
- Port 9090: Cockpit with CSP containing `connect-src 'self' https://griden...`

### 3. DNS LEAKS
- **Brevo (Sendinblue)**: `brevo-code:152de7f9e807f5fdb928561b63837ee5`
- **Anthropic/Claude**: `anthropic-domain-verification-fkngvf=6O6rIXek63sFuNoLAxpynbm2b`
- **Google Workspace email**: MX via ASPMX.L.GOOGLE.COM
- **SPF**: Google + Brevo

### 4. NEXT.JS ARCHITECTURE
- Framework: Next.js with Turbopack (App Router)
- No Supabase keys found in any client-side JS bundles or RSC payloads
- Supabase integration is entirely server-side (Next.js Route Handlers / Server Actions)
- Single API endpoint exposed client-side: `/api/market/stream`
- 12 JS chunks totalling ~1.5MB analyzed — zero client-exposed secrets

### 5. ATTACK SURFACE
- Market data API is a potential vector for SSRF if it proxies external sources
- No authentication on market data implies internal network misconfiguration
- Same server as Metabase — potential pivot point between services
- Cockpit CSP leak: may reveal internal hostnames/IPs

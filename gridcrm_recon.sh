#!/bin/bash
# =========================================
# GRIDCRM RECON & LEAK REPRODUCTION SCRIPT
# =========================================
# Target: Grid Energies ecosystem 
# Usage: bash gridcrm_recon.sh
# =========================================

echo "=========================================="
echo " GRIDCRM RECONNAISSANCE & LEAK CHECKER"
echo "=========================================="
echo ""

BASE="https://app.gridcrm.fr"
HELP="https://help.gridcrm.fr"
STATUS="https://status.gridcrm.fr"
SUPA="https://vvzfgsdbcxbwtczgnyvy.supabase.co"

# 1. CHECK BOOKSTACK (PUBLIC WIKI)
echo "--- [1] BookStack :: Public Knowledge Base ---"
python3 -c "
import urllib.request, re, json
base = '$HELP/books/aide-gridcrm'
pages = ['roles-permissions', 'documents-ged', 'telephonie-webphone', 'marche-energie', 'sniffer', 'vocabulaire-grid', 'referentiels', 'validations-manager', 'comptabilite']
for p in pages:
    try:
        r = urllib.request.Request(f'{base}/page/{p}', headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(r, timeout=5)
        html = resp.read().decode('utf-8')
        m = re.search(r'<main[^>]*>(.*?)</main>', html, re.DOTALL)
        if m:
            text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            text = re.sub(r'\s+', ' ', text)
            print(f'  ✓ {p}: {len(text)} chars of content')
    except:
        print(f'  ✗ {p}: error')

# Check for DPO email
html = urllib.request.urlopen(f'{base}/page/documents-ged', timeout=5).read().decode('utf-8')
emails = re.findall(r'[\w.+-]+@[\w.-]+\.\w+', html)
print(f'  Emails found: {set(emails)}')
"

# 2. CHECK UPTIME KUMA
echo ""
echo "--- [2] Uptime Kuma :: Status Monitor ---"
curl -s "$STATUS/api/entry-page" 2>/dev/null
echo ""
echo ""

# 3. CHECK SUBSONAINS
echo "--- [3] Subdomain Discovery ---"
for sub in dev admin sales adv rh compta manager bureau webphone; do
  code=$(curl -sI -o /dev/null -w "%{http_code}" "https://${sub}.gridcrm.fr" --connect-timeout 3 2>/dev/null)
  echo "  ${sub}.gridcrm.fr → HTTP ${code}"
done

# 4. CHECK ECOSYSTEM
echo ""
echo "--- [4] Grid Energies Ecosystem ---"
for site in gridpilot.fr gridsign.fr gridacademy.fr moncomparatifenergie.fr gridenergies.info; do
  code=$(curl -sI -o /dev/null -w "%{http_code}" "https://${site}" --connect-timeout 3 2>/dev/null)
  echo "  ${site} → HTTP ${code}"
done

# 5. SUPABASE CHECK
echo ""
echo "--- [5] Supabase Backend ---"
curl -s "$SUPA/rest/v1/" -H "Accept: application/json" 2>/dev/null
echo ""
echo ""

# 6. DNS INFO
echo "--- [6] DNS Records ---"
echo "  MX: $(dig +short mx gridcrm.fr 2>/dev/null | tr '\n' ' ')"
echo "  NS: $(dig +short ns gridcrm.fr 2>/dev/null | tr '\n' ' ')"

# 7. SECURITY HEADERS
echo ""
echo "--- [7] Security Headers ---"
curl -sI "$BASE" 2>/dev/null | grep -iE 'strict-transport|content-security|x-frame|x-content|x-xss|referrer|permissions' | head -10

echo ""
echo "=========================================="
echo " SCAN COMPLETE"
echo "=========================================="

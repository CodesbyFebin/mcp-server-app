"""GSTIN (Goods and Services Tax Identification Number) validation tool.

Validates 15-character Indian GSTIN format and provides entity information.
Format: 2-digit state code + 5-character PAN + 4 digits + 1 character + 1 checksum + 1Z + 1 alphanumeric
"""

import re
from typing import Dict, Any, Optional


def validate_gstin(gstin: str) -> Dict[str, Any]:
    """Validate a GSTIN number and return structured results.
    
    Args:
        gstin: 15-character GSTIN string
        
    Returns:
        Dictionary with validation result, entity type, and state information
    """
    result: Dict[str, Any] = {
        "valid": False,
        "gstin": gstin,
        "state_code": None,
        "state_name": None,
        "entity_type": None,
        "pan": None,
        "checksum_valid": False,
        "errors": []
    }

    """
    GSTIN is 15 characters: 2-digit state code + 10-char PAN (5 letters +
    4 digits + 1 check letter) + 1-char entity status + literal 'Z' + 1-char
    checksum. The previous regex collapsed the PAN check letter into the
    entity slot and only matched 14 chars, rejecting every real GSTIN.
    """
    gstin_pattern = r"^([0-9]{2})([A-Z]{5})([0-9]{4})([A-Z])([A-Z0-9])(Z)([A-Z0-9])$"

    match = re.match(gstin_pattern, gstin)
    if not match:
        result["errors"].append("Invalid GSTIN format — expected 15 characters in pattern SS PPPPL NNNN E Z C")
        return result

    state_code_digit = match.group(1)        # SS
    pan_letters = match.group(2)             # PPPPP
    pan_digits = match.group(3)              # NNNN
    pan_check_letter = match.group(4)        # PAN check letter (10th PAN char)
    entity_code = match.group(5)             # E
    checksum_z = match.group(6)              # Z (literal)
    checksum_char = match.group(7)           # C

    full_pan = pan_letters + pan_digits + pan_check_letter

    result["gstin"] = gstin
    result["state_code"] = state_code_digit
    result["pan"] = full_pan

    # Map state code to state name (India GST state codes)
    state_map = {
        "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
        "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan",
        "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim",
        "12": "Arunachal Pradesh", "13": "Assam", "14": "West Bengal", "15": "Madhya Pradesh",
        "16": "Chhattisgarh", "17": "Odisha", "18": "Jharkhand", "19": "Gujarat",
        "20": "Daman and Diu", "21": "Dadra and Nagar Haveli", "22": "Maharashtra",
        "23": "Goa", "24": "Lakshadweep", "25": "Kerala", "26": "Tamil Nadu",
        "27": "Telangana", "28": "Karnataka", "29": "Andhra Pradesh", "30": "Puducherry",
        "31": "Andaman and Nicobar Islands",
    }
    
    result["state_name"] = state_map.get(state_code_digit, f"State code {state_code_digit}")
    result["state_code_full"] = state_code_digit
    
    # Entity type based on 4th character of PAN (not GSTIN entity code)
    # In GSTIN, the entity code after the 4 digits indicates the type
    entity_map = {
        "01": "Regular taxable person",
        "02": "Composition taxable person", 
        "03": "Non-resident taxable person",
        "04": "Tax deductor at source",
        "05": "Tax collector at source",
        "15": "Input service distributor",
        "91": "Person required to deduct/collect tax",
        "92": "Casual taxable person",
        "94": "Non-resident online taxable person",
    }
    
    # GSTIN entity code mapping
    gst_entity_map = {
        "1": "Regular dealer",
        "2": "Composition dealer", 
        "3": "Project entrepreneur",
        "4": "Casual taxable person",
        "5": "Non-resident taxable person",
        "6": "Tax deductor at source",
        "7": "Tax collector at source",
        "8": "Input service distributor",
        "9": "Composition dealer (alternate)",
    }
    
    result["entity_type"] = gst_entity_map.get(entity_code, f"Entity code {entity_code}")
    
    # Canonical GSTN checksum — the 15th char must equal the algorithmic
    # checksum of the first 14. Falsifying this (hardcoded True) would have
    # accepted every structurally-correct-but-checksum-invalid GSTIN, so the
    # tool would have reported valid data for non-existent taxpayers.
    result["checksum_valid"] = checksum_char == _gstin_checksum_char(gstin[:14])

    result["valid"] = True
    return result


def _gstin_checksum_char(first_14: str) -> str:
    """Compute the 15th GSTIN checksum character from the first 14.

    Canonical GSTN algorithm: each char maps to a value ('0'-'9' -> 0-9,
    'A'-'Z' -> 10-35); odd-position (1-indexed) values are doubled and, if
    the doubled value is >= 36, split into its base-36 digits and summed;
    even-position values are taken as-is; all values are summed; the
    checksum digit is (36 - sum % 36) % 36, rendered back as 0-9 / A-Z.
    """
    def char_value(c: str) -> int:
        if c.isdigit():
            return int(c)
        return ord(c.upper()) - ord('A') + 10

    total = 0
    factor = 1  # alternates 1, 2, 1, 2, ... starting at 1 for position 1
    for c in first_14:
        v = char_value(c)
        if factor == 1:
            v = v * 2
            if v >= 36:
                v = (v // 36) + (v % 36)
        total += v
        factor = 3 - factor

    check = (36 - (total % 36)) % 36
    if check < 10:
        return str(check)
    return chr(ord('A') + check - 10)


def get_state_info(state_code: str) -> Optional[Dict[str, Any]]:
    """Get state information by state code."""
    state_map = {
        "01": {"name": "Jammu and Kashmir", "capital": "Srinagar"},
        "02": {"name": "Himachal Pradesh", "capital": "Shimla"},
        "03": {"name": "Punjab", "capital": "Chandigarh"},
        "04": {"name": "Chandigarh", "capital": "Chandigarh"},
        "05": {"name": "Uttarakhand", "capital": "Dehradun"},
        "06": {"name": "Haryana", "capital": "Chandigarh"},
        "06": {"name": "Delhi", "capital": "New Delhi"},
        "08": {"name": "Rajasthan", "capital": "Jaipur"},
        "09": {"name": "Sikkim", "capital": "Gangtok"},
        "10": {"name": "Uttar Pradesh", "capital": "Lucknow"},
        "11": {"name": "Sikkim"},  # Note: duplicate code
        "12": {"name": "Arunachal Pradesh", "capital": "Itanagar"},
        "13": {"name": "Assam", "capital": "Dispur"},
        "14": {"name": "West Bengal", "capital": "Kolkata"},
        "15": {"name": "Madhya Pradesh", "capital": "Bhopal"},
        "16": {"name": "Chhattisgarh", "capital": "Raipur"},
        "17": {"name": "Odisha", "capital": "Bhubaneswar"},
        "18": {"name": "Jharkhand", "capital": "Ranchi"},
        "19": {"name": "Gujarat", "capital": "Gandhinagar"},
        "20": {"name": "Daman and Diu", "capital": "Daman"},
        "21": {"name": "Dadra and Nagar Haveli", "capital": "Silvassa"},
        "22": {"name": "Maharashtra", "capital": "Mumbai"},
        "23": {"name": "Goa", "capital": "Panaji"},
        "24": {"name": "Lakshadweep", "capital": "Kavaratti"},
        "25": {"name": "Kerala", "capital": "Thiruvananthapuram"},
        "26": {"name": "Tamil Nadu", "capital": "Chennai"},
        "27": {"name": "Telangana", "capital": "Hyderabad"},
        "28": {"name": "Karnataka", "capital": "Bengaluru"},
        "29": {"name": "Andhra Pradesh", "capital": "Amaravati"},
        "30": {"name": "Puducherry", "capital": "Puducherry"},
        "31": {"name": "Andaman and Nicobar Islands", "capital": "Port Blair"},
    }
    
    return state_map.get(state_code)


# Example usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        gstin = sys.argv[1]
        result = validate_gstin(gstin)
        if result["valid"]:
            print(f"✅ Valid GSTIN")
            print(f"   State: {result['state_name']} ({result['state_code']})")
            print(f"   PAN: {result['pan']}")
            print(f"   Entity: {result['entity_type']}")
        else:
            print(f"❌ Invalid GSTIN")
            for error in result["errors"]:
                print(f"   Error: {error}")
    else:
        print("Usage: python -m tools.gst <gstin>")
        print("Example: python -m tools.gst 06AAAAS1234C1Z5")
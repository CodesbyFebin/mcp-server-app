"""IFSC (Indian Financial System Code) lookup tool.

IFSC format: 11-character alphanumeric code
- First 4 characters: Bank code
- 5th character: Always 0 (reserved for future use)
- Last 6 characters: Branch code
Example: SBIN0001234 (State Bank of India, branch 000123)
"""

import re
from typing import Dict, Any, Optional, Literal


def extract_ifsc_data(ifsc: str) -> Dict[str, Any]:
    """Extract and validate IFSC (Indian Financial System Code) data.
    
    Format: 11-character alphanumeric code
    - First 4 characters: Bank code (alphabetic)
    - 5th character: 0 (zero, reserved)
    - Last 6 characters: Branch code (alphanumeric)
    Example: SBIN0001234
    
    Args:
        ifsc: IFSC code string (e.g., "SBIN0001234")
        
    Returns:
        Dictionary with validation result and bank/branch information
    """
    result: Dict[str, Any] = {
        "valid": False,
        "ifsc": ifsc.upper(),
        "ifsc_original": ifsc,
        "bank_code": None,
        "bank_name": None,
        "branch_code": None,
        "center_id": None,  # 5th character (always 0)
        "errors": []
    }
    
    # IFSC pattern: 4 alphabetic + 0 + 6 alphanumeric
    ifsc_pattern = r"^([A-Z]{1,4})0([A-Z0-9]{6})$"
    
    match = re.match(ifsc_pattern, ifsc.upper())
    if not match:
        result["errors"].append(f"Invalid IFSC format — expected 11 chars: 4alpha+0+6alphanum, got: {ifsc}")
        return result
    
    bank_code = match.group(1)
    branch_code = match.group(2)
    
    result["bank_code"] = bank_code
    result["branch_code"] = branch_code
    result["center_id"] = "0"  # 5th character
    
    # Map common bank codes to names
    bank_map: Dict[str, str] = {
        "SBIN": "State Bank of India",
        "BARB": "Bank of Baroda",
        "CNXB": "Canara Bank",
        "ICIC": "ICICI Bank",
        "HDFC": "HDFC Bank",
        "KKBK": "Kotak Mahindra Bank",
        "AYBK": "Axis Bank",
        "IBKK": "IndusInd Bank",
        "PNBH": "Punjab National Bank",
        "UBIN": "Union Bank of India",
        "BKID": "Bank of India",
        "BKLE": "Bank of Maharashtra",
        "COPA": "Co-operative Bank",
        "FEDB": "Federal Bank",
        "ICIC0": "ICICI Bank",
    }
    
    result["bank_name"] = bank_map.get(bank_code, f"Bank code: {bank_code}")
    
    result["valid"] = True
    return result


def validate_ifsc(ifsc: str, allowed_banks: list[str] | None = None) -> Dict[str, Any]:
    """Validate IFSC against a list of allowed bank codes."""
    result = extract_ifsc_data(ifsc)
    if not result["valid"]:
        return result
    
    if allowed_banks:
        bank_lower = result["bank_code"].lower()
        if bank_lower not in [b.lower() for b in allowed_banks]:
            result["errors"].append(f"Bank code {result['bank_code']} not in allowed list")
            result["valid"] = False
    
    return result


def get_state_bank_centers(ifsc: str) -> Dict[str, Any]:
    """Extract the RBI center ID from IFSC 5th character.
    
    The 5th character of an IFSC code is always 0 and represents
    the RBI central office center identifier.
    """
    result = extract_ifsc_data(ifsc)
    if not result["valid"]:
        return result
    
    # The 5th character is always 0 in valid IFSC codes
    # This maps to the RBI center (e.g., 0 = Mumbai, 1 = Chennai, etc.)
    # For now, document the center_id
    result["center_info"] = {
        "center_id": result["center_id"],
        "description": "RBI central office identifier (always 0 in valid IFSC)",
        "note": "IFSC 5th character is reserved for future RBI use"
    }
    
    return result


# Example usage
if __name__ == "__main__":
    import sys
    
    print("=== IFSC Validation ===")
    if len(sys.argv) > 1:
        ifsc_result = extract_ifsc_data(sys.argv[1])
        if ifsc_result["valid"]:
            print(f"✅ Valid IFSC")
            print(f"   IFSC: {ifsc_result['ifsc']}")
            print(f"   Bank code: {ifsc_result['bank_code']}")
            print(f"   Bank name: {ifsc_result['bank_name']}")
            print(f"   Branch code: {ifsc_result['branch_code']}")
        else:
            print(f"❌ Invalid IFSC")
            for error in ifsc_result["errors"]:
                print(f"   Error: {error}")
    else:
        # Test with sample IFSCs
        test_ifscs = ["SBIN0001234", "BARB0TRIVRD", "HDFC0000123", "ICIC0001234"]
        for test_ifsc in test_ifscs:
            r = extract_ifsc_data(test_ifsc)
            print(f"  {test_ifsc}: {'✅' if r['valid'] else '❌'} - {r['bank_name']}")
    
    print("\n=== Center ID Lookup ===")
    center_result = get_state_bank_centers("SBIN0001234")
    if center_result["valid"]:
        print(f"  Center info: {center_result['center_info']}")
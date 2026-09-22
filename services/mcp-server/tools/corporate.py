"""PAN (Permanent Account Number) and CIN (Corporate Identification Number) decoder.

PAN format: 5 letters + 4 digits + 1 letter (e.g., ABCDE1234F)
CIN format: 21 characters (e.g., U12345DL2020PLC123456)

Valid entity type identification based on 4th PAN letter.
"""

import re
from typing import Dict, Any, Optional, Literal


def extract_pan_data(pan: str) -> Dict[str, Any]:
    """Extract and validate PAN (Permanent Account Number) data.
    
    Format: 5 uppercase letters + 4 digits + 1 uppercase letter
    Example: ABCDE1234F
    
    The 4th character indicates entity type:
    - P: Individual
    - C: Company
    - H: HUF (Hindu Undivided Family)
    - F: Firm
    - A: Association of Persons
    - T: Trust
    - B: Body of Individuals
    - L: Local Authority
    
    Args:
        pan: PAN number string (e.g., "ABCDE1234F")
        
    Returns:
        Dictionary with validation result and entity type information
    """
    result: Dict[str, Any] = {
        "valid": False,
        "pan": pan.upper(),
        "pan_original": pan,
        "letters": None,
        "digits": None,
        "check_letter": None,
        "entity_type": None,
        "entity_type_hindi": None,
        "errors": []
    }
    
    # PAN pattern: 5 letters + 4 digits + 1 letter
    pan_pattern = r"^([A-Z]{5})(\d{4})([A-Z])$"
    
    match = re.match(pan_pattern, pan.upper())
    if not match:
        result["errors"].append(f"Invalid PAN format — expected 5 letters + 4 digits + 1 letter, got: {pan}")
        return result
    
    letters = match.group(1)
    digits = match.group(2)
    check_letter = match.group(3)
    
    result["letters"] = letters
    result["digits"] = digits
    result["check_letter"] = check_letter
    
    # Determine entity type based on 4th letter (index 3)
    entity_map: Dict[str, Dict[str, Any]] = {
        "P": {
            "entity_type": "Individual",
            "entity_type_hindi": "व्यक्ति",
            "description": "Permanent Account Number for individual taxpayers"
        },
        "C": {
            "entity_type": "Company",
            "entity_type_hindi": "कंपनी",
            "description": "Permanent Account Number for companies"
        },
        "H": {
            "entity_type": "HUF",
            "entity_type_hindi": "एचयूएफ",
            "description": "Hindu Undivided Family"
        },
        "F": {
            "entity_type": "Firm",
            "entity_type_hindi": "फर्म",
            "description": "Firm or partnership"
        },
        "A": {
            "entity_type": "Association of Persons (AOP)",
            "entity_type_hindi": "व्यक्ति संघ",
            "description": "Association of Persons"
        },
        "T": {
            "entity_type": "Trust",
            "entity_type_hindi": "न्यास",
            "description": "Trust"
        },
        "B": {
            "entity_type": "Body of Individuals (BOI)",
            "entity_type_hindi": "व्यक्ति संघ",
            "description": "Body of Individuals"
        },
        "L": {
            "entity_type": "Local Authority",
            "entity_type_hindi": "स्थानीय प्राधिकरण",
            "description": "Local authority such as government body"
        }
    }
    
    fourth_letter = letters[3]
    entity_info = entity_map.get(fourth_letter)
    
    if entity_info:
        result["entity_type"] = entity_info["entity_type"]
        result["entity_type_hindi"] = entity_info["entity_type_hindi"]
    
    result["valid"] = True
    return result


def validate_pan(pan: str, allowed_entity_types: list[str] | None = None) -> Dict[str, Any]:
    """Validate PAN against a list of allowed entity types."""
    result = extract_pan_data(pan)
    if not result["valid"]:
        return result
    
    if allowed_entity_types:
        entity_lower = result["entity_type"].lower()
        if entity_lower not in [e.lower() for e in allowed_entity_types]:
            result["errors"].append(f"Entity type {result['entity_type']} not in allowed list")
            result["valid"] = False
    
    return result


def extract_cin_data(cin: str) -> Dict[str, Any]:
    """Extract and validate CIN (Corporate Identification Number).
    
    Format: U12345DL2020PLC123456 (21 characters)
    - U: Fixed prefix
    - 12345: ROC number (5 digits)
    - DL: State code (2 letters)
    - 2020: Year of incorporation (4 digits)
    - PLC: Company type (3 letters)
    - 123456: Registration number (6 digits)
    
    Args:
        cin: CIN number string (e.g., "U12345DL2020PLC123456")
        
    Returns:
        Dictionary with validation result and company information
    """
    result: Dict[str, Any] = {
        "valid": False,
        "cin": cin,
        "cin_original": cin,
        "roc_number": None,
        "state_code": None,
        "state_name": None,
        "year_of_incorporation": None,
        "company_type": None,
        "registration_number": None,
        "errors": []
    }
    
    # CIN pattern: U + 5 digits + 2 state letters + 4 digits + 3 company type letters + 6 digits
    cin_pattern = r"^U(\d{5})([A-Z]{2})(\d{4})([A-Z]{3})(\d{6})$"
    
    match = re.match(cin_pattern, cin.upper())
    if not match:
        result["errors"].append(f"Invalid CIN format — expected U+5digits+2letters+4digits+3letters+6digits, got: {cin}")
        return result
    
    roc_number = match.group(1)
    state_code = match.group(2)
    year_of_incorporation = match.group(3)
    company_type_code = match.group(4)
    registration_number = match.group(5)
    
    result["roc_number"] = roc_number
    result["state_code"] = state_code
    result["year_of_incorporation"] = year_of_incorporation
    result["company_type"] = company_type_code
    result["registration_number"] = registration_number
    
    # Map state codes to names
    state_map: Dict[str, str] = {
        "DL": "Delhi",
        "UP": "Uttar Pradesh",
        "MH": "Maharashtra",
        "KA": "Karnataka",
        "GJ": "Gujarat",
        "TN": "Tamil Nadu",
        "AP": "Andhra Pradesh",
        "TR": "Telangana",
        "KR": "Kerala",
        "RJ": "Rajasthan",
        "PB": "Punjab",
        "HR": "Haryana",
        "CT": "Chhattisgarh",
        "JH": "Jharkhand",
        "UP": "Uttar Pradesh",
        "WB": "West Bengal",
        "OD": "Odisha",
        "AS": "Assam",
        "MP": "Madhya Pradesh",
        "BR": "Bihar",
        "NN": "None (Union Territory)",
    }
    
    result["state_name"] = state_map.get(state_code, f"State/UT: {state_code}")
    
    # Map company type codes
    company_type_map: Dict[str, str] = {
        "PLC": "Public Limited Company",
        "PVT": "Private Limited Company",
        "LLP": "Limited Liability Partnership",
        "OPC": "One Person Company",
        "FTC": "Foreign Trading Company",
        "Govt": "Government Company",
    }
    
    result["company_type_full"] = company_type_map.get(company_type_code, f"Company type: {company_type_code}")
    
    result["valid"] = True
    return result


def validate_cin(cin: str, allowed_company_types: list[str] | None = None) -> Dict[str, Any]:
    """Validate CIN against a list of allowed company types."""
    result = extract_cin_data(cin)
    if not result["valid"]:
        return result
    
    if allowed_company_types:
        company_lower = result["company_type"].lower()
        if company_lower not in [c.lower() for c in allowed_company_types]:
            result["errors"].append(f"Company type {result['company_type']} not in allowed list")
            result["valid"] = False
    
    return result


# Example usage
if __name__ == "__main__":
    import sys
    
    print("=== PAN Validation ===")
    if len(sys.argv) > 1:
        pan_result = extract_pan_data(sys.argv[1])
        if pan_result["valid"]:
            print(f"✅ Valid PAN")
            print(f"   PAN: {pan_result['pan']}")
            print(f"   Name: {pan_result['entity_type']}")
            print(f"   4th char (entity): {pan_result['letters'][3]}")
            print(f"   digits: {pan_result['digits']}")
            print(f"   check letter: {pan_result['check_letter']}")
        else:
            print(f"❌ Invalid PAN")
            for error in pan_result["errors"]:
                print(f"   Error: {error}")
    else:
        # Test with sample PANs
        test_pans = ["ABCDE1234F", "PAN1234567A", "ABCDP12345"]
        for test_pan in test_pans:
            r = extract_pan_data(test_pan)
            print(f"  {test_pan}: {'✅' if r['valid'] else '❌'} - {r['entity_type']}")
    
    print("\n=== CIN Validation ===")
    if len(sys.argv) > 2:
        cin_path = sys.argv[2] if len(sys.argv) > 2 else "U12345DL2020PLC123456"
        cin_result = extract_cin_data(cin_path)
        if cin_result["valid"]:
            print(f"✅ Valid CIN")
            print(f"   CIN: {cin_result['cin']}")
            print(f"   ROC: {cin_result['roc_number']}")
            print(f"   State: {cin_result['state_name']}")
            print(f"   Year: {cin_result['year_of_incorporation']}")
            print(f"   Company type: {cin_result['company_type_full']}")
            print(f"   Registration: {cin_result['registration_number']}")
        else:
            print(f"❌ Invalid CIN")
            for error in cin_result["errors"]:
                print(f"   Error: {error}")
    else:
        # Test with sample CIN
        cin_result = extract_cin_data("U12345DL2020PLC123456")
        print(f"  U12345DL2020PLC123456: {'✅' if cin_result['valid'] else '❌'}")
        if cin_result["valid"]:
            print(f"    ROC: {cin_result['roc_number']}, State: {cin_result['state_name']}")
#!/usr/bin/env python3
"""Acceptance test harness for FastMCP India enterprise tools.

Drives gst/payments/corporate/banking validators with real-format inputs and
asserts the validator logic is correct. This is runtime acceptance evidence —
not syntax, not types — that proves the tools actually decode the inputs they
claim to decode.

Run:  python3 services/mcp-server/tools/tools_acceptance_test.py
"""

import os
import sys
from pathlib import Path

# Make the service root importable so `from tools.gst import ...` resolves.
SERVICE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVICE_ROOT))
sys.path.insert(0, str(SERVICE_ROOT / "tools"))

from tools.gst import validate_gstin
from tools.payments import validate_upi
from tools.corporate import extract_pan_data, extract_cin_data
from tools.banking import extract_ifsc_data

PASS = 0
FAIL = 0
FAILURES = []


def check(name, got, expected):
    global PASS, FAIL
    if got == expected:
        PASS += 1
        print(f"  PASS  {name}: got {got!r}")
    else:
        FAIL += 1
        FAILURES.append((name, got, expected))
        print(f"  FAIL  {name}: got {got!r}  expected {expected!r}")


def check_truthy(name, field, got):
    global PASS, FAIL
    if got:
        PASS += 1
        print(f"  PASS  {name}.{field}: {got!r}")
    else:
        FAIL += 1
        FAILURES.append((f"{name}.{field} truthy", got, "truthy"))
        print(f"  FAIL  {name}.{field}: empty/falsy, got {got!r}")


def check_false(name, field, got):
    global PASS, FAIL
    if not got:
        PASS += 1
        print(f"  PASS  {name}.{field}: {got!r} (falsy as expected)")
    else:
        FAIL += 1
        FAILURES.append((f"{name}.{field} falsy", got, "falsy"))
        print(f"  FAIL  {name}.{field}: expected falsy, got {got!r}")


print("=" * 60)
print("GSTIN VALIDATION")
print("=" * 60)

# Real-format GSTIN: 27 = Maharashtra (per GST GSTN state list)
g = validate_gstin("27AAAPL1234C1Z5")
print(f"\nInput: 27AAAPL1234C1Z5")
check_truthy("GST valid", "valid", g["valid"])
check("GST state_code", g["state_code"], "27")
check("GST pan extracted", g["pan"], "AAAPL")

# Reject malformed GSTIN (too short)
g_bad = validate_gstin("27AAAPL1234")
print(f"\nInput (malformed, short): 27AAAPL1234")
check_false("GST invalid short", "valid", g_bad["valid"])
check_truthy("GST invalid short errors", "errors", g_bad["errors"])

# Reject GSTIN missing the mandatory Z at position 13
g_no_z = validate_gstin("27AAAPL1234C1X5")  # X instead of Z
print(f"\nInput (no Z at pos 13): 27AAAPL1234C1X5")
check_false("GST missing Z", "valid", g_no_z["valid"])

print()
print("=" * 60)
print("UPI VPA VALIDATION")
print("=" * 60)

u = validate_upi("user@okaxis")
print(f"\nInput: user@okaxis")
check_truthy("UPI valid", "valid", u["valid"])
check("UPI user", u["user"], "user")
check("UPI handle", u["handle"], "@okaxis")
check("UPI bank", u["bank"], "Axis Bank")

u2 = validate_upi("john.doe_99@sbi")
print(f"\nInput: john.doe_99@sbi")
check_truthy("UPI2 valid", "valid", u2["valid"])
check("UPI2 handle", u2["handle"], "@sbi")

# Reject malformed VPA (missing @)
u_bad = validate_upi("userokaxis")
print(f"\nInput (no @): userokaxis")
check_false("UPI no-at", "valid", u_bad["valid"])

# Reject empty user
u_empty = validate_upi("@okaxis")
print(f"\nInput (empty user): @okaxis")
check_false("UPI empty user", "valid", u_empty["valid"])

print()
print("=" * 60)
print("PAN DECODING")
print("=" * 60)

# ABCDE1234F — 4th letter 'D' is not in the entity map (P/C/H/F/A/T/B/L).
# A real individual PAN has 4th char 'P', e.g. ABCDP1234F.
p = extract_pan_data("ABCDP1234F")
print(f"\nInput: ABCDP1234F (4th char P = Individual)")
check_truthy("PAN valid", "valid", p["valid"])
check("PAN entity_type", p["entity_type"], "Individual")
check("PAN 4th letter", p["letters"][3], "P")
check("PAN digits", p["digits"], "1234")

p_c = extract_pan_data("ABCDT1234K")
print(f"\nInput: ABCDT1234K (4th char T = Trust)")
check("PAN Trust entity", p_c["entity_type"], "Trust")

# Reject 9-char PAN
p_bad = extract_pan_data("ABCDP1234")
print(f"\nInput (9 chars): ABCDP1234")
check_false("PAN 9-char", "valid", p_bad["valid"])

print()
print("=" * 60)
print("CIN DECODING")
print("=" * 60)

# U12345DL2020PLC123456 — DL = Delhi
c = extract_cin_data("U12345DL2020PLC123456")
print(f"\nInput: U12345DL2020PLC123456")
check_truthy("CIN valid", "valid", c["valid"])
check("CIN roc", c["roc_number"], "12345")
check("CIN state_code", c["state_code"], "DL")
check("CIN state_name", c["state_name"], "Delhi")
check("CIN year", c["year_of_incorporation"], "2020")
check("CIN reg", c["registration_number"], "123456")

c_bad = extract_cin_data("U12345DL2020PLC")  # truncated
print(f"\nInput (truncated): U12345DL2020PLC")
check_false("CIN truncated", "valid", c_bad["valid"])

print()
print("=" * 60)
print("IFSC DECODING")
print("=" * 60)

i = extract_ifsc_data("SBIN0001234")
print(f"\nInput: SBIN0001234")
check_truthy("IFSC valid", "valid", i["valid"])
check("IFSC bank_code", i["bank_code"], "SBIN")
check("IFSC bank_name", i["bank_name"], "State Bank of India")
check("IFSC branch", i["branch_code"], "0001234")
check("IFSC center_id", i["center_id"], "0")

i2 = extract_ifsc_data("HDFC0001234")
print(f"\nInput: HDFC0001234")
check("IFSC2 bank", i2["bank_name"], "HDFC Bank")

i_bad = extract_ifsc_data("SB1X0001234")  # digit in bank code
print(f"\nInput (non-alpha bank code): SB1X0001234")
check_false("IFSC bad bank", "valid", i_bad["valid"])

# Reject IFSC where 5th char is not 0
i_no0 = extract_ifsc_data("SBIN1001234")
print(f"\nInput (5th char not 0): SBIN1001234")
check_false("IFSC no-zero", "valid", i_no0["valid"])

print()
print("=" * 60)
print(f"ACCEPTANCE RESULTS: {PASS} passed, {FAIL} failed")
print("=" * 60)
if FAIL:
    print("\nFAILURES:")
    for name, got, exp in FAILURES:
        print(f"  {name}: got={got!r} expected={exp!r}")
    sys.exit(1)
print("\nALL TOOL ACCEPTANCE TESTS PASSED")

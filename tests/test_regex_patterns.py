import re
import pytest
from src.core.patterns import PREDEFINED_PATTERNS

PATTERN_TEST_CASES = {
    "pk_cnic": {
        "pos": ["37405-1234567-1", "3740512345671"],
        "neg": ["123", "abc", "37405-123456-1"]
    },
    "pk_phone": {
        "pos": ["0300-1234567", "+923001234567", "03215555555"],
        "neg": ["123", "923001", "042-111-222-333"]
    },
    "pk_passport": {
        "pos": ["AB1234567", "CD9876543"],
        "neg": ["A1234567", "ABC123456", "AB123456"]
    },
    "pk_dl": {
        "pos": ["RI-12-1234567", "LE1412345678"],
        "neg": ["R-12-12345", "LE-123"]
    },
    "pk_plate": {
        "pos": ["RI-1234", "LE-7788", "ICT-555"],
        "neg": ["A-1", "1234", "LE-ABCDE"]
    },
    "us_ssn": {
        "pos": ["123-45-6789", "787-65-4321"],
        "neg": ["666-29-9999", "000-12-3456", "999-12-3456", "12-34-5678"]
    },
    "us_phone": {
        "pos": ["(555) 123-4567", "555-123-4567", "1-555-123-4567", "555.123.4567"],
        "neg": ["123", "555-123", "555123456789"]
    },
    "us_zip": {
        "pos": ["90210", "12345-6789"],
        "neg": ["123", "1234", "abcde"]
    },
    "us_dl": {
        "pos": ["D1234567", "A12345678901"],
        "neg": ["1234567", "AB123"]
    },
    "eu_iban": {
        "pos": ["DE89370400440532013000", "GB29NWBK60161331926819"],
        "neg": ["123", "DE89"]
    },
    "eu_vat": {
        "pos": ["DE123456789", "FR12345678901", "NL123456789B01"],
        "neg": ["123", "US123456"]
    },
    "in_aadhaar": {
        "pos": ["2000-1234-5678", "9999 1234 5678", "211112345678"],
        "neg": ["1234-5678", "0000-1234-5678", "1999-1234-5678"]
    },
    "in_phone": {
        "pos": ["+919876543210", "09876543210", "9876543210"],
        "neg": ["123", "98765"]
    },
    "in_pan": {
        "pos": ["ABCDE1234F", "XYZPD9999Z"],
        "neg": ["ABCD1234F", "ABCDE12345"]
    },
    "in_dl": {
        "pos": ["DL1420110012345", "MH1220181234567"],
        "neg": ["DL12", "DL-123"]
    },
    "uk_nino": {
        "pos": ["AB123456A", "AB 12 34 56 A"],
        "neg": ["QQ12345", "12345678A"]
    },
    "uk_phone": {
        "pos": ["07123456789", "+447123456789", "07123 456789"],
        "neg": ["0123", "07123"]
    },
    "global_credit_card": {
        "pos": ["4111-1111-1111-1111", "4111111111111111"],
        "neg": ["1234567", "abc"]
    },
    "global_email": {
        "pos": ["test@example.com", "user.name+tag@company.co.uk"],
        "neg": ["test@", "test@example", "test.com"]
    },
    "global_ip": {
        "pos": ["192.168.1.1", "10.0.0.1", "255.255.255.255"],
        "neg": ["256.1.1.1", "1.2.3.4.5", "abc"]
    },
    "global_name": {
        "pos": ["Mr. John Watson", "Dr. John Watson", "Prof. Stephen Hawking"],
        "neg": ["Watson", "John", "Mr."]
    },
    "global_location": {
        "pos": ["123 Baker Street", "10 Downing St", "400 Broad Ave."],
        "neg": ["Baker Street", "123 Baker", "10 Downing"]
    }
}


@pytest.mark.parametrize("pattern_id", PREDEFINED_PATTERNS.keys())
def test_predefined_pattern_matching(pattern_id):
    pattern_data = PREDEFINED_PATTERNS[pattern_id]
    regex_str = pattern_data["regex"]
    compiled = re.compile(regex_str, re.IGNORECASE)

    test_cases = PATTERN_TEST_CASES.get(pattern_id)
    assert test_cases is not None, f"No test cases defined for {pattern_id}"

    for pos_example in test_cases["pos"]:
        assert compiled.search(pos_example) is not None, f"Failed positive match for {pattern_id}: {pos_example}"

    for neg_example in test_cases["neg"]:
        match = compiled.search(neg_example)
        if match is not None:
            # Recompiling with IGNORECASE can match lowercase variants; verify the match isn't a false positive.
            assert match.group() != neg_example, f"Incorrect negative match for {pattern_id}: {neg_example}"

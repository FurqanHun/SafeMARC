# Predefined pattern definitions for SafeMARC curated regular expression library

PREDEFINED_PATTERNS = {
    "pk_cnic": {
        "label": "PK CNIC",
        "regex": r"\b\d{5}[- ]?\d{7}[- ]?\d\b",
        "keywords": ["cnic", "identity", "card", "nic", "citizen", "national", "pakistan"],
        "regions": ["Pakistan"]
    },
    "pk_phone": {
        "label": "PK Phone",
        "regex": r"\b(?:\+?92[- ]?)?0?3\d{2}[- ]?\d{7}\b",
        "keywords": ["phone", "mobile", "cell", "tel", "contact", "number", "call"],
        "regions": ["Pakistan"]
    },
    "pk_passport": {
        "label": "PK Passport",
        "regex": r"\b[A-Z]{2}\d{7}\b",
        "keywords": ["passport", "travel", "document", "identity", "dgip", "pakistan"],
        "regions": ["Pakistan"]
    },
    "pk_dl": {
        "label": "PK Driving License",
        "regex": r"\b[A-Z]{2}[- ]?\d{2}[- ]?\d{7,8}\b",
        "keywords": ["driving", "license", "dl", "licence", "permit", "vehicle", "pakistan"],
        "regions": ["Pakistan"]
    },
    "pk_plate": {
        "label": "PK Vehicle Plate",
        "regex": r"\b[A-Z]{2,3}[- ]?\d{3,4}\b",
        "keywords": ["plate", "vehicle", "registration", "car", "number", "motor", "pakistan"],
        "regions": ["Pakistan"]
    },
    "us_ssn": {
        "label": "US SSN",
        "regex": r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b",
        "keywords": ["ssn", "social security", "tax", "tin", "sec", "payroll"],
        "regions": ["United States"]
    },
    "us_phone": {
        "label": "US Phone",
        "regex": r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b",
        "keywords": ["phone", "mobile", "cell", "tel", "contact", "number", "office", "call"],
        "regions": ["United States"]
    },
    "us_zip": {
        "label": "US Zip Code",
        "regex": r"\b\d{5}(?:-\d{4})?\b",
        "keywords": ["zip", "postal", "address", "state", "delivery", "mail"],
        "regions": ["United States"]
    },
    "us_dl": {
        "label": "US Driver's License",
        "regex": r"\b(?=.*\d)(?=.*[A-Z])[A-Z0-9]{9,12}\b",
        "keywords": ["license", "dl", "licence", "permit", "driver", "dmv", "vehicle"],
        "regions": ["United States"]
    },
    "eu_iban": {
        "label": "EU IBAN",
        "regex": r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}(?:[A-Z0-9]?){0,16}\b",
        "keywords": ["iban", "bank", "account", "transfer", "wire", "deposit", "bic", "swift"],
        "regions": ["European Union"]
    },
    "eu_vat": {
        "label": "EU VAT ID",
        "regex": r"\b[A-Z]{2}\s?(?=.*\d)[A-Z0-9]{2,12}\b",
        "keywords": ["vat", "tax", "tin", "business", "company", "registration", "eu"],
        "regions": ["European Union"]
    },
    "in_aadhaar": {
        "label": "IN Aadhaar",
        "regex": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        "keywords": ["aadhaar", "uid", "identity", "card", "citizen", "india", "uidai"],
        "regions": ["India"]
    },
    "in_phone": {
        "label": "IN Phone",
        "regex": r"\b(?:\+?91[- ]?)?0?[6-9]\d{2}[- ]?\d{3}[- ]?\d{4}\b|\b(?:\+?91[- ]?)?0?[6-9]\d{9}\b",
        "keywords": ["phone", "mobile", "cell", "tel", "contact", "number", "call"],
        "regions": ["India"]
    },
    "in_pan": {
        "label": "IN PAN Card",
        "regex": r"\b[A-Z]{5}\d{4}[A-Z]\b",
        "keywords": ["pan", "tax", "permanent account", "income", "card", "india"],
        "regions": ["India"]
    },
    "in_dl": {
        "label": "IN Driving License",
        "regex": r"\b[A-Z]{2}[- ]?\d{2}[- ]?\d{11}\b",
        "keywords": ["driving", "license", "dl", "licence", "permit", "driver", "india"],
        "regions": ["India"]
    },
    "uk_nino": {
        "label": "UK NINO",
        "regex": r"\b[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z]\s*\d{2}\s*\d{2}\s*\d{2}\s*[A-D]?\b",
        "keywords": ["nino", "national insurance", "tax", "insurance", "hmrc", "payroll"],
        "regions": ["United Kingdom"]
    },
    "uk_phone": {
        "label": "UK Phone",
        "regex": r"\b(?:\+?44[- ]?|0)7\d{3}[- ]?\d{6}\b|\b(?:\+?44[- ]?|0)7\d{9}\b|\b(?:\+?44[- ]?|0)7\d{2}[- ]?\d{3}[- ]?\d{4}\b",
        "keywords": ["phone", "mobile", "cell", "tel", "contact", "number", "call"],
        "regions": ["United Kingdom"]
    },
    "global_credit_card": {
        "label": "Credit Card",
        "regex": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        "keywords": ["credit", "card", "visa", "mastercard", "cc", "amex", "payment", "debit"],
        "regions": ["Global"]
    },
    "global_email": {
        "label": "Email",
        "regex": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b",
        "keywords": ["email", "mail", "contact", "e-mail", "address"],
        "regions": ["Global"]
    },
    "global_ip": {
        "label": "IP Address",
        "regex": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        "keywords": ["ip", "address", "host", "server", "ipv4", "dns"],
        "regions": ["Global"]
    },
    "global_passport": {
        "label": "Passport No",
        "regex": r"\b(?=[A-Z0-9]*\d)(?=[A-Z0-9]*[A-Z])[A-Z0-9]{6,9}\b",
        "keywords": ["passport", "document", "travel", "visa", "border", "identity", "no"],
        "regions": ["Global"]
    }
}

REGIONS = ["Global", "Pakistan", "United States", "European Union", "India", "United Kingdom"]

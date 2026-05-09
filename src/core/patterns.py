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
        "regex": r"\b(?:03\d{2}[- ]?\d{7})|(?:\+92[- ]?3\d{2}[- ]?\d{7})\b",
        "keywords": ["phone", "mobile", "cell", "tel", "contact", "number", "call"],
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
    "eu_iban": {
        "label": "EU IBAN",
        "regex": r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}(?:[A-Z0-9]?){0,16}\b",
        "keywords": ["iban", "bank", "account", "transfer", "wire", "deposit", "bic", "swift"],
        "regions": ["European Union"]
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
    }
}

REGIONS = ["Global", "Pakistan", "United States", "European Union"]

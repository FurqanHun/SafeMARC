import pytest
from src.core.detectors.text import RegexDetector
from src.core.patterns import PREDEFINED_PATTERNS


def make_mock_ocr_data(words_list):
    data = {
        "text": [],
        "level": [],
        "block_num": [],
        "par_num": [],
        "line_num": [],
        "left": [],
        "top": [],
        "width": [],
        "height": [],
        "conf": []
    }
    for i, word in enumerate(words_list):
        data["text"].append(word)
        data["level"].append(5)
        data["block_num"].append(1)
        data["par_num"].append(1)
        data["line_num"].append(1)
        data["left"].append(i * 50)
        data["top"].append(10)
        data["width"].append(40)
        data["height"].append(15)
        data["conf"].append(95.0)
    return data


def test_luhn_credit_card_validation():
    detector = RegexDetector()
    pattern_info = PREDEFINED_PATTERNS["global_credit_card"]
    detector.add_custom_pattern(
        label=pattern_info["label"],
        pattern=pattern_info["regex"],
        is_regex=True,
        keywords=pattern_info["keywords"]
    )

    # Use a standard Visa number to verify the Luhn positive match.
    valid_card_data = make_mock_ocr_data(["My", "card", "is", "4111-1111-1111-1111"])
    hits = detector._scan_data_dict(valid_card_data, scale=1.0)
    assert len(hits) == 1
    assert hits[0].label == "Credit Card"
    assert hits[0].confidence == 95.0

    # Mutate the last digit to trigger a Luhn checksum failure.
    invalid_card_data = make_mock_ocr_data(["My", "card", "is", "4111-1111-1111-1112"])
    hits = detector._scan_data_dict(invalid_card_data, scale=1.0)
    assert len(hits) == 0


def test_mod97_iban_validation():
    detector = RegexDetector()
    pattern_info = PREDEFINED_PATTERNS["eu_iban"]
    detector.add_custom_pattern(
        label=pattern_info["label"],
        pattern=pattern_info["regex"],
        is_regex=True,
        keywords=pattern_info["keywords"]
    )

    # Use a valid German IBAN for the mod-97 check.
    valid_iban_data = make_mock_ocr_data(["IBAN", "is", "DE89370400440532013000"])
    hits = detector._scan_data_dict(valid_iban_data, scale=1.0)
    assert len(hits) == 1
    assert hits[0].label == "EU IBAN"
    assert hits[0].confidence == 95.0

    # Mutate check digits to verify the rejection.
    invalid_iban_data = make_mock_ocr_data(["IBAN", "is", "DE89370400440532013009"])
    hits = detector._scan_data_dict(invalid_iban_data, scale=1.0)
    assert len(hits) == 0


def test_proximity_keyword_confidence_boost():
    detector = RegexDetector()
    pattern_info = PREDEFINED_PATTERNS["us_ssn"]
    detector.add_custom_pattern(
        label=pattern_info["label"],
        pattern=pattern_info["regex"],
        is_regex=True,
        keywords=pattern_info["keywords"]
    )

    # The context window contains 'security', boosting confidence to 90%.
    boosted_data = make_mock_ocr_data(["My", "social", "security", "number", "is", "123-45-6789"])
    hits = detector._scan_data_dict(boosted_data, scale=1.0)
    assert len(hits) == 1
    assert hits[0].confidence == 90.0

    # Missing context keywords drop the confidence to the default (25%).
    unboosted_data = make_mock_ocr_data(["The", "serial", "code", "listed", "is", "123-45-6789"])
    hits = detector._scan_data_dict(unboosted_data, scale=1.0)
    assert len(hits) == 1
    assert hits[0].confidence == 25.0

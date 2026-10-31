from backend.security.data_leak_detector import DataLeakDetector


def test_email_and_api_key_detection():
    detector = DataLeakDetector()
    text = "Reach alice.smith@example.com and use token sk_live_ABCDEF1234567890 for the API."
    result = detector.detect(text)
    assert result["has_sensitive_data"] is True
    assert any(item["type"] == "EMAIL" for item in result["findings"])
    assert any(item["type"] == "API_KEY" for item in result["findings"])
    assert "***" in result["findings"][0]["redacted_example"]


def test_confidential_keywords_are_detected():
    detector = DataLeakDetector()
    result = detector.detect("The customer password must not be exposed in logs.")
    assert result["has_sensitive_data"] is True
    assert any(item["type"] == "CONFIDENTIAL_KEYWORD" for item in result["findings"])


def test_borderline_inputs_are_safe():
    detector = DataLeakDetector()
    result = detector.detect("This is a harmless summary of the product launch plan.")
    assert result["has_sensitive_data"] is False
    assert result["findings"] == []

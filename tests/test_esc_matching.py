import pytest
from datetime import date, timedelta


def test_strip_prefix_removes_aws():
    from lambda_handler import strip_prefix
    assert strip_prefix("AWS Lambda") == "Lambda"


def test_strip_prefix_removes_amazon():
    from lambda_handler import strip_prefix
    assert strip_prefix("Amazon S3") == "S3"


def test_strip_prefix_leaves_bare_name():
    from lambda_handler import strip_prefix
    assert strip_prefix("EC2 Image Builder") == "EC2 Image Builder"
    assert strip_prefix("Elastic Load Balancing") == "Elastic Load Balancing"
    assert strip_prefix("Service Quotas") == "Service Quotas"


def test_strip_prefix_strips_whitespace():
    from lambda_handler import strip_prefix
    assert strip_prefix("  AWS  Config") == "Config"


def test_esc_matching_prefixless_services():
    """3 services in esc_services.json have no prefix — they must still match."""
    from lambda_handler import strip_prefix
    esc_services = {"EC2 Image Builder", "Elastic Load Balancing", "Service Quotas"}
    normalized_esc = {strip_prefix(s) for s in esc_services}

    # These are the full_name values that come from the Directory API
    full_names_from_api = [
        "AWS EC2 Image Builder",
        "Elastic Load Balancing",
        "Amazon Service Quotas",
    ]
    for full_name in full_names_from_api:
        assert strip_prefix(full_name) in normalized_esc, \
            f"{full_name!r} should match ESC list after normalization"


def test_esc_matching_non_esc_service_excluded():
    from lambda_handler import strip_prefix
    esc_services = {"AWS Lambda", "Amazon S3"}
    normalized_esc = {strip_prefix(s) for s in esc_services}
    assert strip_prefix("Amazon RDS") not in normalized_esc


def test_check_esc_freshness_returns_none_when_fresh():
    fresh_date = date.today().isoformat()
    from lambda_handler import check_esc_freshness
    assert check_esc_freshness(fresh_date) is None


def test_check_esc_freshness_warns_when_stale():
    stale_date = (date.today() - timedelta(days=60)).isoformat()
    from lambda_handler import check_esc_freshness
    result = check_esc_freshness(stale_date)
    assert result is not None
    assert "60" in result or "days old" in result


def test_check_esc_freshness_returns_none_for_empty():
    from lambda_handler import check_esc_freshness
    assert check_esc_freshness("") is None
    assert check_esc_freshness(None) is None


def test_normalize_for_esc_strips_parenthetical():
    """_normalize_for_esc removes trailing (ACRONYM) suffixes before matching."""
    from lambda_handler import _normalize_for_esc
    assert _normalize_for_esc("AWS Key Management Service (KMS)") == "Key Management Service"
    assert _normalize_for_esc("Amazon Simple Storage Service (S3)") == "Simple Storage Service"
    assert _normalize_for_esc("AWS Cloud Development Kit (AWS CDK)") == "Cloud Development Kit"


def test_esc_aliases_cover_abbreviated_names():
    """EC2/VPC/RDS/VPN must match their ESC full-name equivalents via alias dict."""
    from lambda_handler import _ESC_NAME_ALIASES, _normalize_for_esc
    # Build a fake normalized_esc matching what docs.aws.eu returns
    esc_entries = {
        "Amazon Elastic Compute Cloud",
        "Amazon Virtual Private Cloud",
        "Amazon Relational Database Service",
        "AWS Virtual Private Network",
    }
    normalized_esc = {_normalize_for_esc(s) for s in esc_entries}

    for short_name in ["EC2", "VPC", "RDS", "VPN"]:
        alias = _ESC_NAME_ALIASES.get(_normalize_for_esc(short_name))
        assert alias in normalized_esc, f"{short_name!r} alias {alias!r} not in normalized ESC"

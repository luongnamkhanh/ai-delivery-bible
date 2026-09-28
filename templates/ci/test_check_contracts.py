"""Test âm cho evaluator: mỗi rule phải có ít nhất 1 case FAIL và 1 case PASS.
Chạy: python3 -m pytest ci -q  (từ root repo)."""
import check_contracts as cc


def _x1(text):
    return list(cc.x1_no_floating_image_tags("x.yaml", text))


def test_x1_flags_latest_and_missing_tag():
    assert _x1("image: nginx:latest")
    assert _x1("image: nginx")
    assert _x1("image: registry.local:5000/app")          # ':' chỉ là port → vẫn thiếu tag
    assert _x1("  - image: 'quay.io/strimzi/kafka:latest'")


def test_x1_passes_pinned():
    assert not _x1("image: nginx:1.27.1")
    assert not _x1("image: registry.local:5000/app:1.2.3")
    assert not _x1("image: app@sha256:0123abcd")


def test_every_rule_in_yml_has_evaluator():
    ids = {r["id"] for r in cc.RULES_YML["rules"]}
    assert ids <= set(cc.RULES), f"thiếu evaluator cho {ids - set(cc.RULES)}"

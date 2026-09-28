#!/usr/bin/env python3
"""Contract evaluator — chạy rulepack contracts/rules.yml lên file trong scope.
Không guide, chỉ rule: mỗi FAIL in rõ rule id + file + lý do. Exit 1 nếu có FAIL.
Usage: python3 ci/check_contracts.py [file ...]   (mặc định: scope_default trong rules.yml)
Thêm rule = 1 entry trong rules.yml + 1 hàm trong RULES dưới đây + 1 test âm trong test_check_contracts.py.
"""
import glob, pathlib, re, sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
RULES_YML = yaml.safe_load((ROOT / "contracts/rules.yml").read_text())
P = RULES_YML.get("params") or {}
WAIVERS = RULES_YML.get("waivers") or {}

IMAGE_RE = re.compile(r"^\s*-?\s*image:\s*['\"]?([^'\"\s#]+)", re.M)  # cho cả dòng list "- image:"


def x1_no_floating_image_tags(path, text):
    """image phải có tag cụ thể; cấm :latest và thiếu tag. Digest (@sha256:...) coi là pin."""
    for img in IMAGE_RE.findall(text):
        if "@sha256:" in img:
            continue
        name, _, tag = img.rpartition(":")
        # không có ':' → không tag; ':' chỉ là port registry (tag chứa '/') → cũng không tag
        if not name or "/" in tag or tag == "latest":
            yield f"image '{img}' không pin tag"


RULES = {
    "X1-no-floating-image-tags": x1_no_floating_image_tags,
}


def _rel(path):
    p = pathlib.Path(path).resolve()
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)


def check(path):
    rel = _rel(path)
    text = pathlib.Path(path).read_text()
    fails = []
    for rule in RULES_YML["rules"]:
        fn = RULES.get(rule["id"])
        if fn is None:
            fails.append(f"{rule['id']}: khai trong rules.yml nhưng chưa có evaluator")
            continue
        if rel in (WAIVERS.get(rule["id"]) or {}):
            continue
        fails += [f"{rule['id']}: {msg}" for msg in fn(rel, text)]
    return fails


def main(argv):
    files = argv or [
        f for pat in RULES_YML["scope_default"]
        for f in glob.glob(str(ROOT / pat), recursive=True)
        if "/contracts/" not in f and "/ci/" not in f and "/.git/" not in f
    ]
    bad = 0
    for f in sorted(files):
        for msg in check(f):
            print(f"FAIL {_rel(f)} — {msg}")
            bad += 1
    print(f"{'FAIL' if bad else 'OK'} {len(RULES_YML['rules'])} rule × {len(files)} file, {bad} vi phạm")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])

#!/usr/bin/env python3
"""Runtime evaluator — chạy các check trong contracts/runtime.yml CÓ `cmd` (read-only, qua kubectl exec).
So kết quả: expect_re (mọi regex phải match) · expect_not_re (không regex nào được match) ·
expect_max (số đầu tiên trong output <= ngưỡng). Check chưa có cmd → SKIP có tên (spec). Exit 1 nếu có FAIL.
Usage: KUBECONFIG=... python3 ci/check_runtime.py [RT-id ...]
"""
import pathlib, re, subprocess, sys
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKS = yaml.safe_load((ROOT / "contracts/runtime.yml").read_text())["checks"]


def run(check, timeout=90):
    r = subprocess.run(["bash", "-c", check["cmd"]], capture_output=True, text=True, timeout=timeout)
    out = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        return False, f"cmd exit {r.returncode}: {out[-300:]}"
    for pat in check.get("expect_re", []):
        if not re.search(pat, out, re.M):
            return False, f"thiếu /{pat}/ trong output: {out[-300:]}"
    for pat in check.get("expect_not_re", []):
        m = re.search(pat, out, re.M)
        if m:
            return False, f"vi phạm /{pat}/: '{m.group(0)}'"
    if "expect_max" in check:
        m = re.search(r"-?\d+(\.\d+)?", out)
        if not m:
            return False, f"không có số trong output (bảng rỗng/NULL?): {out[-300:]}"
        if float(m.group(0)) > float(check["expect_max"]):
            return False, f"{m.group(0)} > {check['expect_max']}"
    return True, (out.splitlines()[0][:120] if out else "")


def main():
    want = set(sys.argv[1:])
    bad = 0
    for c in CHECKS:
        if want and c["id"] not in want:
            continue
        if "cmd" not in c:
            print(f"SKIP {c['id']} (spec — chưa có cmd)")
            continue
        try:
            ok, msg = run(c)
        except subprocess.TimeoutExpired:
            ok, msg = False, "timeout"
        print(f"{'PASS' if ok else 'FAIL'} {c['id']} {msg}")
        bad += not ok
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

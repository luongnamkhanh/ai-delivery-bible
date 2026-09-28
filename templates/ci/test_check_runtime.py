"""Runner — test không cần cluster: cmd=echo, kiểm 3 kiểu expect."""
import check_runtime as rt


def test_expect_re_and_not_re():
    ok, _ = rt.run({"cmd": "echo 'retention.ms=259200000'",
                    "expect_re": [r"retention\.ms=259200000"],
                    "expect_not_re": [r"retention\.ms=(?!259200000\b)[0-9]+"]})
    assert ok
    ok, msg = rt.run({"cmd": "echo 'retention.ms=86400000'",
                      "expect_not_re": [r"retention\.ms=(?!259200000\b)[0-9]+"]})
    assert not ok and "vi phạm" in msg


def test_expect_max():
    assert rt.run({"cmd": "echo 7", "expect_max": 15})[0]
    assert not rt.run({"cmd": "echo 42", "expect_max": 15})[0]
    assert not rt.run({"cmd": "echo NULL", "expect_max": 15})[0]


def test_cmd_failure_is_fail():
    ok, msg = rt.run({"cmd": "false"})
    assert not ok and "exit" in msg

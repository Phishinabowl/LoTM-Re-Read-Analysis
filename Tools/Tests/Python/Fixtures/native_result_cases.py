"""Deliberate failures: explicit adapter verification only; excluded from default discovery."""

import os
import sys

import pytest

CASE = os.environ.get("NATIVE_FAILURE_CASE", "pass")
if CASE == "collection":
    raise RuntimeError("Synthetic discovery failure <&> é")


@pytest.fixture(autouse=True)
def owned_teardown():
    yield
    if CASE == "teardown":
        raise RuntimeError("Synthetic teardown failure <&> é")


@pytest.mark.xfail(CASE == "xpass", strict=True, reason="Synthetic strict XPASS")
def test_native_case():
    print("native stdout <&> é")
    print("native stderr <&> é", file=sys.stderr)
    if CASE == "assertion":
        assert False, "Synthetic assertion failure <&> é"
    if CASE == "skip":
        pytest.skip("Synthetic unexpected required skip <&> é")
    if CASE == "xfail":
        pytest.xfail("Synthetic unauthorized xfail")
    if CASE == "cancellation":
        raise KeyboardInterrupt


if CASE == "empty":
    del test_native_case

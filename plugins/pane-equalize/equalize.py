#!/usr/bin/env python3
"""Equalize leaf pane areas in the current Herdr tab.

The layout is a binary split tree. Giving each child a share proportional to
the number of leaf panes below it makes every leaf receive the same area while
preserving pane ids, PTYs, processes, focus, and split topology.
"""

from __future__ import annotations

import json
import math
import os
import socket
import sys
from typing import Any


MIN_RATIO = 0.1
MAX_RATIO = 0.9


class HerdrApiError(RuntimeError):
    pass


def api_request(method: str, params: dict[str, Any]) -> dict[str, Any]:
    socket_path = os.environ.get("HERDR_SOCKET_PATH", "").strip()
    if not socket_path:
        raise HerdrApiError("HERDR_SOCKET_PATH is not set")

    request_id = f"pane-equalize:{os.getpid()}:{method}"
    payload = json.dumps(
        {"id": request_id, "method": method, "params": params},
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(3.0)
        client.connect(socket_path)
        client.sendall(payload)
        response_data = bytearray()
        while b"\n" not in response_data:
            chunk = client.recv(65536)
            if not chunk:
                break
            response_data.extend(chunk)

    if not response_data:
        raise HerdrApiError(f"empty response from {method}")

    try:
        response = json.loads(response_data.split(b"\n", 1)[0])
    except json.JSONDecodeError as error:
        raise HerdrApiError(f"invalid response from {method}: {error}") from error

    if "error" in response:
        error = response["error"]
        code = error.get("code", "api_error")
        message = error.get("message", "unknown Herdr API error")
        raise HerdrApiError(f"{method}: {code}: {message}")

    result = response.get("result")
    if not isinstance(result, dict):
        raise HerdrApiError(f"missing result from {method}")
    return result


def target_params() -> dict[str, str]:
    pane_id = os.environ.get("HERDR_PANE_ID", "").strip()
    if pane_id:
        return {"pane_id": pane_id}

    tab_id = os.environ.get("HERDR_TAB_ID", "").strip()
    if tab_id:
        return {"tab_id": tab_id}

    return {}


def collect_ratios(
    node: dict[str, Any], path: tuple[bool, ...] = ()
) -> tuple[int, list[tuple[list[bool], float, float]]]:
    node_type = node.get("type")
    if node_type == "pane":
        return 1, []
    if node_type != "split":
        raise HerdrApiError(f"unknown layout node type: {node_type!r}")

    first_count, first_updates = collect_ratios(node["first"], path + (False,))
    second_count, second_updates = collect_ratios(node["second"], path + (True,))
    total_count = first_count + second_count
    ideal_ratio = first_count / total_count
    target_ratio = max(MIN_RATIO, min(MAX_RATIO, ideal_ratio))
    current_ratio = float(node.get("ratio", 0.5))

    # Children come first. Ratio changes do not alter paths, but this ordering
    # keeps each subtree internally balanced before its parent is resized.
    updates = first_updates + second_updates
    updates.append((list(path), target_ratio, current_ratio))
    return total_count, updates


def equalize() -> int:
    target = target_params()
    export_result = api_request("layout.export", target)
    layout = export_result.get("layout")
    if not isinstance(layout, dict) or not isinstance(layout.get("root"), dict):
        raise HerdrApiError("layout.export returned no layout tree")

    pane_count, updates = collect_ratios(layout["root"])
    changed = [
        (path, ratio)
        for path, ratio, current in updates
        if not math.isclose(ratio, current, rel_tol=0.0, abs_tol=1e-6)
    ]
    if not changed:
        print(f"pane layout already equalized ({pane_count} pane(s))")
        return 0

    tab_id = layout.get("tab_id")
    if not isinstance(tab_id, str) or not tab_id:
        raise HerdrApiError("layout.export returned no tab id")

    for path, ratio in changed:
        api_request(
            "layout.set_split_ratio",
            {"tab_id": tab_id, "path": path, "ratio": ratio},
        )

    print(f"equalized {pane_count} panes across {len(changed)} split(s)")
    return 0


def self_test() -> int:
    tree = {
        "type": "split",
        "ratio": 0.7,
        "first": {"type": "pane"},
        "second": {
            "type": "split",
            "ratio": 0.8,
            "first": {"type": "pane"},
            "second": {"type": "pane"},
        },
    }
    count, updates = collect_ratios(tree)
    by_path = {tuple(path): target for path, target, _ in updates}
    assert count == 3
    assert math.isclose(by_path[()], 1 / 3)
    assert math.isclose(by_path[(True,)], 1 / 2)
    print("self-test passed")
    return 0


def main() -> int:
    try:
        if sys.argv[1:] == ["--self-test"]:
            return self_test()
        if sys.argv[1:]:
            raise HerdrApiError("usage: equalize.py [--self-test]")
        return equalize()
    except (HerdrApiError, KeyError, TypeError, ValueError, OSError) as error:
        print(f"pane equalize failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/opt/homebrew/bin/python3.14
"""Move one member of a vertical pane pair to its partner's right, without closing it."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import tempfile


class MoveError(RuntimeError):
    pass


class Herdr:
    def __init__(self, socket_path: str):
        self.socket_path = socket_path

    def call(self, method: str, params: dict) -> dict:
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(8)
            connection.connect(self.socket_path)
            request = {"id": "hyper-pane-break", "method": method, "params": params}
            connection.sendall(json.dumps(request).encode() + b"\n")
            with connection.makefile("rb") as reader:
                response = json.loads(reader.readline())
        if "error" in response:
            raise MoveError(f"{method}: {response['error']['message']}")
        return response["result"]

    def layout(self, pane: str) -> dict:
        return self.call("layout.export", {"pane_id": pane})["layout"]

    def move(self, pane: str, destination: dict, focus: bool = False) -> None:
        result = self.call("pane.move", {
            "pane_id": pane, "destination": destination, "focus": focus,
        })["move_result"]
        if not result["changed"]:
            raise MoveError(f"pane move refused: {result.get('reason')}")


def pane_id(node: dict) -> str | None:
    return node.get("pane_id") if node["type"] == "pane" else None


def parent_of(node: dict, pane: str, path: tuple = ()) -> tuple | None:
    if node["type"] == "pane":
        return None
    for second, key in [(False, "first"), (True, "second")]:
        child = node[key]
        if pane_id(child) == pane:
            return node, path, second
        found = parent_of(child, pane, path + (second,))
        if found:
            return found
    return None


def topology(node: dict):
    if node["type"] == "pane":
        return pane_id(node)
    return node["direction"], topology(node["first"]), topology(node["second"])


def ratios(node: dict, equalize: bool, path: tuple = ()) -> tuple[int, list]:
    if node["type"] == "pane":
        return 1, []
    first, a = ratios(node["first"], equalize, path + (False,))
    second, b = ratios(node["second"], equalize, path + (True,))
    value = max(0.1, min(0.9, first / (first + second))) if equalize else node["ratio"]
    updates = a + b
    if not equalize or not math.isclose(value, node["ratio"], abs_tol=1e-6):
        updates.append((list(path), value))
    return first + second, updates


def apply_ratios(api: Herdr, layout: dict, equalize: bool) -> None:
    for path, ratio in ratios(layout["root"], equalize)[1]:
        api.call("layout.set_split_ratio", {
            "tab_id": layout["tab_id"], "path": path, "ratio": ratio,
        })


def is_right_pair(layout: dict, pane: str, partner: str, tab: str) -> bool:
    found = parent_of(layout["root"], pane)
    return bool(layout["tab_id"] == tab and found and found[0]["direction"] == "right"
                and pane_id(found[0]["first"]) == partner
                and pane_id(found[0]["second"]) == pane)


def restore(api: Herdr, pane: str, partner: str, original: dict, was_second: bool) -> None:
    current = api.layout(pane)
    if current["tab_id"] == original["tab_id"]:
        if topology(current["root"]) != topology(original["root"]):
            raise MoveError("배치가 다른 작업으로 변경되어 자동 복원을 중단했습니다.")
        apply_ratios(api, original, False)
        return
    if current["workspace_id"] != original["workspace_id"] or pane_id(current["root"]) != pane:
        raise MoveError("pane이 임시 탭 밖으로 이동해 자동 복원을 중단했습니다.")
    if api.layout(partner)["tab_id"] != original["tab_id"]:
        raise MoveError("원래 짝 pane이 이동해 자동 복원을 중단했습니다.")
    api.move(pane, {"type": "tab", "tab_id": original["tab_id"],
                    "target_pane_id": partner, "split": "down"}, focus=True)
    if not was_second:
        result = api.call("pane.swap", {"source_pane_id": pane, "target_pane_id": partner})
        if not result["swap"]["changed"]:
            raise MoveError("원래 위아래 순서를 복원하지 못했습니다.")
    if topology(api.layout(pane)["root"]) != topology(original["root"]):
        raise MoveError("다른 배치 변경이 있어 원래 비율의 적용을 중단했습니다.")
    apply_ratios(api, original, False)


def break_right(api: Herdr, pane: str) -> str:
    original = api.layout(pane)
    if original["zoomed"]:
        return "Hyper+Z로 확대를 해제한 다음 다시 눌러 주세요."
    found = parent_of(original["root"], pane)
    if not found or found[0]["direction"] != "down":
        return "바로 위·아래 짝 pane이 없습니다. 배치를 유지했습니다."
    parent, _, was_second = found
    partner = pane_id(parent["first" if was_second else "second"])
    if not partner:
        return "짝 영역이 여러 pane입니다. 단순한 상하 두 pane 묶음에서 사용해 주세요."
    try:
        api.move(pane, {"type": "new_tab", "workspace_id": original["workspace_id"],
                        "label": "pane-break"})
        api.move(pane, {"type": "tab", "tab_id": original["tab_id"],
                        "target_pane_id": partner, "split": "right"}, focus=True)
    except (MoveError, OSError, ValueError) as error:
        # A lost response can follow a successful move; inspect before recovery.
        try:
            if not is_right_pair(api.layout(pane), pane, partner, original["tab_id"]):
                restore(api, pane, partner, original, was_second)
                raise MoveError(f"이동 실패. 원래 배치로 복원했습니다: {error}") from error
        except (OSError, ValueError) as recovery_error:
            raise MoveError(f"이동 상태 확인 실패. {pane}은 닫지 않았습니다: {recovery_error}") from error
    try:
        current = api.layout(pane)
        if not is_right_pair(current, pane, partner, original["tab_id"]):
            raise MoveError("이동 후 배치가 달라 균등화를 중단했습니다.")
        apply_ratios(api, current, True)
    except (MoveError, OSError, ValueError) as error:
        raise MoveError(f"오른쪽 이동은 완료됐습니다. 크기는 Hyper+Space로 맞춰 주세요: {error}") from error
    return "선택한 pane을 오른쪽으로 분리하고 크기를 맞췄습니다."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pane", default=os.environ.get("HERDR_ACTIVE_PANE_ID"))
    args = parser.parse_args()
    socket_path = os.environ.get("HERDR_SOCKET_PATH", "")
    if not args.pane or not socket_path:
        parser.error("an explicit pane and HERDR_SOCKET_PATH are required")
    api = Herdr(socket_path)
    key = hashlib.sha256(socket_path.encode()).hexdigest()[:16]
    lock_path = Path(tempfile.gettempdir()) / f"herdr-pane-break-{os.getuid()}-{key}.lock"
    with lock_path.open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        code = 0
        try:
            message = break_right(api, args.pane)
        except (MoveError, OSError, ValueError, KeyError) as error:
            message, code = str(error), 1
        print(message)
        try:
            api.call("notification.show", {"title": "Pane 오른쪽 분리", "body": message, "sound": "none"})
        except (MoveError, OSError, ValueError):
            pass
        return code


if __name__ == "__main__":
    raise SystemExit(main())

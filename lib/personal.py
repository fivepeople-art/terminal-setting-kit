"""The person's own terminal-setting settings: ~/.config/terminal-setting/settings.toml.

One file holds every choice the person makes (Hyper key, 한/A tap, changed
shortcuts, Ghostty look, Herdr options). Updates never touch it; the kit
renders its files from the kit defaults plus this file. Names the person and
their Claude use (`font-size`, `sidebar-width`, ...) live in LOOK; anything
else can still be set by its own name (`ghostty.KEY`, `herdr.TABLE.KEY`).
"""

from __future__ import annotations

import json
import re
import tomllib
from typing import Any, Callable, NamedTuple


class SettingError(ValueError):
    pass


class Setting(NamedTuple):
    where: str  # "top", "ghostty" or "herdr"
    key: str  # top-level name, Ghostty key, or Herdr "table.key"
    parse: Callable[[str], Any]
    ko: str
    default: str


def _int(low: int, high: int) -> Callable[[str], int]:
    def parse(text: str) -> int:
        try:
            value = int(str(text).strip())
        except ValueError:
            raise SettingError(f"숫자로 씁니다({low}~{high})") from None
        if not low <= value <= high:
            raise SettingError(f"{low}~{high} 사이로 씁니다")
        return value
    parse.hint = f"{low}~{high}"
    return parse


def _float(low: float, high: float) -> Callable[[str], float]:
    def parse(text: str) -> float:
        try:
            value = float(str(text).strip())
        except ValueError:
            raise SettingError(f"숫자로 씁니다({low}~{high})") from None
        if not low <= value <= high:
            raise SettingError(f"{low}~{high} 사이로 씁니다")
        return value
    parse.hint = f"{low}~{high}"
    return parse


def _choice(*options: str) -> Callable[[str], str]:
    def parse(text: str) -> str:
        value = str(text).strip()
        if value not in options:
            raise SettingError(f"{' / '.join(options)} 중 하나로 씁니다")
        return value
    parse.hint = " / ".join(options)
    parse.options = options
    return parse


def _bool(text: str) -> bool:
    value = str(text).strip().lower()
    if value in ("on", "true", "yes", "y", "켬", "켜기", "예", "네", "1"):
        return True
    if value in ("off", "false", "no", "n", "끔", "끄기", "아니오", "아니요", "0"):
        return False
    raise SettingError("켬(on) 또는 끔(off)으로 씁니다")


_bool.hint = "켬 / 끔"
_bool.options = ("on", "off")


def _text(text: str) -> str:
    value = str(text).strip()
    if not value or "\n" in value:
        raise SettingError("한 줄 글자로 씁니다")
    return value


LOOK: dict[str, Setting] = {
    "hyper-key": Setting("top", "hyper", _choice("caps_lock", "right_option"), "Hyper 키로 쓸 키(caps_lock=한/A, right_option=오른쪽 Option)", "caps_lock"),
    "hangul-tap": Setting("top", "tap_switches_input", _bool, "Hyper 키를 혼자 눌렀다 떼면 한영 전환", "설치 때 답"),
    "claude-auto-approve": Setting("top", "claude_auto_approve", _bool, "Claude가 명령·파일 작업을 묻지 않고 바로 실행", "on"),
    "font-size": Setting("ghostty", "font-size", _int(8, 40), "글자 크기", "16"),
    "font": Setting("ghostty", "font-family", _text, "글꼴 이름(Mac에 깔린 글꼴)", "Geist Mono"),
    "opacity": Setting("ghostty", "background-opacity", _float(0.3, 1.0), "창 불투명도(1.0=불투명)", "1.0"),
    "cursor": Setting("ghostty", "cursor-style", _choice("block", "bar", "underline"), "커서 모양", "block"),
    "padding": Setting("ghostty", "window-padding-x", _int(0, 40), "창 좌우 여백(위아래는 ghostty.window-padding-y)", "8"),
    "sidebar-width": Setting("herdr", "ui.sidebar_width", _int(12, 30), "사이드바 너비(칸)", "20"),
    "confirm-close": Setting("herdr", "ui.confirm_close", _bool, "스페이스·마지막 탭 닫기 전에 묻기", "on"),
    "notifications": Setting("herdr", "ui.toast.delivery", _choice("herdr", "system", "terminal", "off"), "알림 방식(herdr=창 안, system=macOS 알림, off=끔)", "herdr"),
}
# Tables the kit renders itself; changing them by name would bypass the
# shortcut bridge (keys) or the theme bundle (theme).
HERDR_MANAGED = ("keys", "theme")
GHOSTTY_MANAGED = ("keybind", "command", "theme", "config-file")
# Ghostty appends to these lists; a new value must reset the list first.
GHOSTTY_LISTS = {"font-family": ["Apple SD Gothic Neo"]}


def empty() -> dict[str, Any]:
    return {"hyper": "caps_lock", "tap_switches_input": False, "keys": {}, "ghostty": {}, "herdr": {}}


def loads(text: str) -> dict[str, Any]:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise SettingError(f"설정 파일 형식이 틀렸습니다: {error}") from None
    result = empty()
    for key, value in data.items():
        if key in ("keys", "ghostty"):
            if not isinstance(value, dict):
                raise SettingError(f"[{key}] 아래에는 이름 = 값 줄만 씁니다")
            result[key] = dict(value)
        elif key == "herdr":
            result["herdr"] = {f"{table}.{name}": v for table, values in _flatten(value).items() for name, v in values.items()}
        else:
            result[key] = value
    return result


def _flatten(tree: dict[str, Any], prefix: str = "") -> dict[str, dict[str, Any]]:
    """{"ui": {"sidebar_width": 25, "toast": {"delivery": "off"}}} -> {"ui": {...}, "ui.toast": {...}}"""
    out: dict[str, dict[str, Any]] = {}
    for key, value in tree.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            out.update(_flatten(value, f"{name}."))
        else:
            table, _, leaf = name.rpartition(".")
            out.setdefault(table, {})[leaf] = value
    return out


def literal(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    raise SettingError(f"{value!r}: 글자·숫자·켬/끔만 저장합니다")


def dumps(data: dict[str, Any], actions: list[tuple[str, str, str]]) -> str:
    """Write the file back with its guide comments. actions: (id, default chord, 설명)."""
    lines = [
        "# terminal-setting 내 설정: 업데이트해도 이 파일은 그대로 남습니다.",
        "# 바꾸는 법(쉬운 순서): Claude에게 \"글자 크게 해줘\"처럼 말하기 → `terminal-setting customize`(메뉴)",
        "#   → `terminal-setting set font-size 18` → 이 파일을 직접 고치고 `terminal-setting apply`.",
        "# 이름 목록과 지금 값: `terminal-setting settings`",
        "",
        f"hyper = {literal(data.get('hyper', 'caps_lock'))}  # Hyper 키: caps_lock(한/A) 또는 right_option(오른쪽 Option)",
        f"tap_switches_input = {literal(bool(data.get('tap_switches_input', False)))}  # Hyper 키를 혼자 눌렀다 떼면 한영 전환",
    ]
    extra = {k: v for k, v in data.items() if k not in ("hyper", "tap_switches_input", "keys", "ghostty", "herdr")}
    lines += [f"{k} = {literal(v)}" for k, v in extra.items()]
    lines += ["", "[keys]", "# 동작 = \"키\"(hyper+… 또는 cmd+…, \"\"는 끄기). 바꾼 것만 적습니다. 탭 번호(Cmd+1~9)는 고정."]
    keys = data.get("keys", {})
    for action, chord in keys.items():
        lines.append(f"{action} = {literal(chord)}")
    for action, default, ko in actions:
        if action not in keys:
            lines.append(f"# {action} = \"{default}\"  # {ko}")
    lines += ["", "[ghostty]", "# Ghostty 설정 이름 = 값(예: font-size = 18). 같은 이름을 여러 번 쓰는 설정(keybind 등)은 ~/.config/ghostty/local에."]
    for key, value in data.get("ghostty", {}).items():
        lines.append(f"{json.dumps(key)} = {literal(value)}" if not re.fullmatch(r"[A-Za-z0-9_-]+", key) else f"{key} = {literal(value)}")
    by_table: dict[str, dict[str, Any]] = {}
    for dotted, value in data.get("herdr", {}).items():
        table, _, leaf = dotted.rpartition(".")
        by_table.setdefault(table, {})[leaf] = value
    lines += ["", "# Herdr 설정: [herdr.표] 아래 이름 = 값(예: [herdr.ui] sidebar_width = 24). keys·theme 표는 kit이 만듭니다."]
    for table, values in by_table.items():
        lines += ["", f"[herdr.{table}]"]
        lines += [f"{leaf} = {literal(value)}" for leaf, value in values.items()]
    return "\n".join(lines) + "\n"


def resolve(name: str) -> Setting:
    """A LOOK name, or ghostty.KEY / herdr.TABLE.KEY for anything else."""
    if name in LOOK:
        return LOOK[name]
    where, _, rest = name.partition(".")
    if where == "ghostty" and rest:
        if rest in GHOSTTY_MANAGED:
            raise SettingError(f"{rest}는 kit이 만듭니다. 단축키는 `terminal-setting key`, 테마는 `terminal-setting theme`")
        return Setting("ghostty", rest, _guess, f"Ghostty {rest}", "")
    if where == "herdr" and "." in rest:
        if rest.split(".")[0] in HERDR_MANAGED:
            raise SettingError(f"{rest}는 kit이 만듭니다. 단축키는 `terminal-setting key`, 테마는 `terminal-setting theme`")
        return Setting("herdr", rest, _guess, f"Herdr {rest}", "")
    names = ", ".join(LOOK)
    raise SettingError(f"{name!r}: 없는 이름입니다. 쓸 수 있는 이름: {names} (그 밖은 ghostty.이름, herdr.표.이름)")


def _guess(text: str) -> Any:
    value = str(text).strip()
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    for kind in (int, float):
        try:
            return kind(value)
        except ValueError:
            pass
    return _text(value)


def set_value(data: dict[str, Any], name: str, raw: str) -> Any:
    setting = resolve(name)
    try:
        value = setting.parse(raw)
    except SettingError as error:
        raise SettingError(f"{name}: {error}") from None
    if setting.where == "top":
        data[setting.key] = value
    else:
        data[setting.where][setting.key] = value
    return value


def unset_value(data: dict[str, Any], name: str) -> bool:
    setting = resolve(name)
    if setting.where == "top":
        return data.pop(setting.key, None) is not None
    return data[setting.where].pop(setting.key, None) is not None


def current_value(data: dict[str, Any], name: str) -> Any:
    setting = resolve(name)
    if setting.where == "top":
        return data.get(setting.key)
    return data[setting.where].get(setting.key)


# ---------------------------------------------------------------- rendering into kit files


def ghostty_lines(data: dict[str, Any]) -> list[str]:
    lines = []
    for key, value in data.get("ghostty", {}).items():
        shown = ("true" if value else "false") if isinstance(value, bool) else str(value)
        if key in GHOSTTY_LISTS:
            lines.append(f'{key} = ""')
            lines.append(f"{key} = {shown}")
            lines += [f"{key} = {fallback}" for fallback in GHOSTTY_LISTS[key] if fallback != shown]
        else:
            lines.append(f"{key} = {shown}")
    return lines


def set_table_scalar(text: str, table: str, key: str, value: Any) -> str:
    lines = text.splitlines(keepends=True)
    header = f"[{table}]"
    start = next((i for i, line in enumerate(lines) if line.strip() == header), None)
    entry = f"{key} = {literal(value)}\n"
    if start is None:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        return "".join(lines) + f"\n{header}\n{entry}"
    end = next((i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith("[")), len(lines))
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for i in range(start + 1, end):
        if pattern.match(lines[i]):
            lines[i] = entry
            return "".join(lines)
    insert = start + 1
    for i in range(start + 1, end):
        if lines[i].strip() and not lines[i].lstrip().startswith("#"):
            insert = i + 1
    lines.insert(insert, entry)
    return "".join(lines)


def apply_herdr(text: str, data: dict[str, Any]) -> str:
    for dotted, value in data.get("herdr", {}).items():
        table, _, key = dotted.rpartition(".")
        text = set_table_scalar(text, table, key, value)
    parsed = tomllib.loads(text)
    for dotted, value in data.get("herdr", {}).items():
        node: Any = parsed
        for part in dotted.split("."):
            node = node.get(part) if isinstance(node, dict) else None
        if node != value:
            raise SettingError(f"Herdr 설정 {dotted}를 넣지 못했습니다")
    return text


# ---------------------------------------------------------------- hand edits of kit files


def ghostty_hand_lines(current: str, rendered: str) -> list[str]:
    """Setting lines the person added or changed in the kit's Ghostty config."""
    known = {line.strip() for line in rendered.splitlines()}
    out = []
    for line in current.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped in known or "=" not in stripped:
            continue
        out.append(stripped)
    return out


def herdr_hand_values(current: str, rendered: str) -> tuple[dict[str, Any], bool]:
    """Scalar Herdr options the person changed by hand, and whether anything
    else (shortcuts, theme, lists) changed that cannot be carried over."""
    try:
        now, before = tomllib.loads(current), tomllib.loads(rendered)
    except tomllib.TOMLDecodeError:
        return {}, True
    now_flat, before_flat = _scalars(now), _scalars(before)
    moved = {k: v for k, v in now_flat.items() if before_flat.get(k, object()) != v and k.split(".")[0] not in HERDR_MANAGED}
    rest_now = {k: v for k, v in _all_leaves(now).items() if k not in moved}
    rest_before = {k: v for k, v in _all_leaves(before).items() if k not in moved}
    return moved, rest_now != rest_before


def _scalars(tree: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    out = {}
    for key, value in tree.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            out.update(_scalars(value, f"{name}."))
        elif isinstance(value, (str, int, float, bool)) and "." in name:
            out[name] = value
    return out


def _all_leaves(tree: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    out = {}
    for key, value in tree.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            out.update(_all_leaves(value, f"{name}."))
        else:
            out[name] = json.dumps(value, sort_keys=True, default=str)
    return out

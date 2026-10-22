#!/usr/bin/env python3.14
"""terminal-setting: install, keep and remove the terminal-setting-kit terminal on this Mac.

The kit owns the files it writes (Ghostty and Herdr config, themes, the
Karabiner rule it adds). The person owns ~/.config/terminal-setting/settings.toml and
~/.config/ghostty/local; updates never touch those. A kit-owned file the person
edited by hand is backed up before it is rewritten, and the run says where.

Source: the system repository's kit/ (generated into terminal-setting-kit by
scripts/export_kit.py); edit it there, never in an installed copy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT / "lib"))
import keymap_render as keymap  # noqa: E402
import personal  # noqa: E402

REPO = "fivepeople-art/terminal-setting-kit"
# Homebrew 7 asks "Do you want to proceed?" before each install unless this is
# set; the person already agreed to the install (install.sh sets it too).
os.environ.setdefault("HOMEBREW_NO_ASK", "1")
AUTO_TITLE = ("kryptamine/herdr-auto-title", "v0.14.0")
LOCAL_PLUGINS = ("confirm-close", "pane-equalize")
PLUGIN_IDS = ("confirm-close", "terminal-setting.pane-equalize", "herdr.auto-title")
CLAUDE_THEME = "custom:terminal-setting"
# macOS shortcut 61 is "Select next source in Input menu"; F18 is key code 79,
# 8388608 the function-key flag macOS records for F-keys.
INPUT_HOTKEY_ID = "61"
INPUT_HOTKEY = {"enabled": True, "value": {"parameters": [65535, 79, 8388608], "type": "standard"}}
# macOS's own "Select next source" shortcut, Ctrl+Option+Space (32 = space
# character, 49 = space key code, 786432 = Control + Option).
INPUT_HOTKEY_DEFAULT = {"enabled": True, "value": {"parameters": [32, 49, 786432], "type": "standard"}}
PROFILE_BEGIN = "# >>> terminal-setting >>>"
PROFILE_END = "# <<< terminal-setting <<<"

ACTIONS_KO = {
    "pane_break_right": "짝 pane을 오른쪽으로 옮기기",
    "pane_left": "왼쪽 pane으로",
    "pane_right": "오른쪽 pane으로",
    "workspace_previous": "이전 스페이스",
    "workspace_next": "다음 스페이스",
    "agent_previous_alias": "이전 에이전트(보조 키)",
    "tab_previous": "이전 탭",
    "tab_next": "다음 탭",
    "agent_previous_or_pane_up": "이전 에이전트",
    "agent_next_or_pane_down": "다음 에이전트",
    **{f"tab_{n}": f"{n}번 탭" for n in range(1, 10)},
    "workspace_picker": "스페이스 고르기",
    "goto_or_window_tree": "바로 가기(에이전트·탭 찾기)",
    "workspace_new": "새 스페이스(홈 폴더에서)",
    "workspace_close": "스페이스 닫기",
    "tab_new": "새 탭",
    "tab_close": "탭 닫기(확인 뒤)",
    "pane_split": "pane 나누기",
    "pane_close": "pane 닫기(확인 뒤)",
    "pane_close_alias": "pane 닫기(보조 키)",
    "help": "단축키 도움말",
    "pane_zoom": "pane 크게 보기",
    "pane_resize_left": "pane 경계를 왼쪽으로",
    "pane_resize_down": "pane 경계를 아래로",
    "pane_resize_up": "pane 경계를 위로",
    "pane_resize_right": "pane 경계를 오른쪽으로",
    "pane_equalize": "pane 크기 똑같이",
    "yazi": "파일 탐색기(yazi)",
    "scroll_bottom_or_copy_exit": "맨 아래로 스크롤",
    "notification_target": "알림 온 곳으로 가기",
    "theme_toggle": "테마 바꾸기",
    "pane_rename": "pane 이름 바꾸기",
    "settings": "Herdr 설정",
    "detach": "Herdr 잠시 떼기(detach)",
    "reload": "Herdr 설정 다시 읽기",
    "workspace_rename": "스페이스 이름 바꾸기",
    "tab_rename": "탭 이름 바꾸기",
    "worktree_new": "새 git worktree",
    "sidebar_toggle": "사이드바 보이기·숨기기",
}


class Fail(RuntimeError):
    pass


# ---------------------------------------------------------------- places


def home() -> Path:
    return Path(os.environ["HOME"])


def paths() -> dict[str, Path]:
    h = home()
    return {
        "ghostty": h / ".config/ghostty/config",
        "ghostty_local": h / ".config/ghostty/local",
        "ghostty_themes": h / ".config/ghostty/themes",
        "herdr": h / ".config/herdr/config.toml",
        "herdr_bin": h / ".local/bin/herdr",
        "auto_title": h / ".config/herdr-auto-title/config.env",
        "karabiner": h / ".config/karabiner/karabiner.json",
        "claude_dir": h / ".claude",
        "claude_settings": h / ".claude/settings.json",
        "claude_theme": h / ".claude/themes/terminal-setting.json",
        "statusline": h / ".claude/terminal-setting/statusline.sh",
        "skill": h / ".claude/skills/terminal-setting",
        "reply_style": h / ".claude/output-styles/i-have-adhd.md",
        "herdr_skill": h / ".claude/skills/herdr/SKILL.md",
        "settings": h / ".config/terminal-setting/settings.toml",
        "rendered": h / ".local/state/terminal-setting/rendered",
        "state": h / ".local/state/terminal-setting/state.json",
        "backups": h / ".local/state/terminal-setting/backups",
        "bin": h / ".local/bin/terminal-setting",
        "zprofile": h / ".zprofile",
    }


def kit_version() -> str:
    path = KIT / "VERSION"
    return path.read_text(encoding="utf-8").strip() if path.exists() else "dev"


def themes() -> list[str]:
    return [name for name in keymap.KIT.theme_names if (KIT / "themes" / name).is_dir()]


# ---------------------------------------------------------------- state and owned files


def load_state() -> dict[str, Any]:
    path = paths()["state"]
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"files": {}, "originals": {}, "ours": {}}


def save_state(state: dict[str, Any]) -> None:
    write_atomic(paths()["state"], json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_atomic(path: Path, text: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def backup(path: Path, state: dict[str, Any], why: str) -> Path:
    stamp = state.setdefault("_stamp", datetime.now().strftime("%Y%m%d-%H%M%S"))
    target = paths()["backups"] / stamp / path.relative_to(home())
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    state.setdefault("_notes", []).append(f"{why}: {path} → {target}")
    return target


def write_owned(path: Path, text: str, state: dict[str, Any], mode: int = 0o644) -> None:
    """Write a kit-owned file; keep the person's version first if there is one."""
    key = str(path)
    if path.is_symlink():
        if key not in state["originals"]:
            state["originals"][key] = str(backup(path, state, "설치 전 파일 보관")) if path.exists() else "absent"
        path.unlink()
    if path.exists():
        current = path.read_text(encoding="utf-8", errors="replace")
        if current == text:
            state["files"][key] = digest(text)
            return
        if key not in state["originals"]:
            state["originals"][key] = str(backup(path, state, "설치 전 파일 보관"))
        elif state["files"].get(key) != digest(current):
            backup(path, state, "손으로 고친 것 보관(다시 옮기려면 Claude에게 이 백업을 보여 주세요)")
    else:
        state["originals"].setdefault(key, "absent")
    write_atomic(path, text, mode)
    state["files"][key] = digest(text)


# ---------------------------------------------------------------- commands we call


def run(cmd: list[str], *, check: bool = False, input: str | None = None) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, input=input)
    except FileNotFoundError as error:
        result = subprocess.CompletedProcess(cmd, 127, "", str(error))
    if check and result.returncode != 0:
        raise Fail(f"{' '.join(cmd)} 실패: {(result.stderr or result.stdout).strip()[-400:]}")
    return result


def run_shown(cmd: list[str]) -> int:
    """Run with the terminal attached (installers that ask for a password)."""
    return subprocess.call(cmd)


# The kit was tried with this Herdr; an older one is left alone and a new one
# goes to ~/.local/bin beside it.
HERDR_MIN = (0, 9, 5)


def herdr_version(binary: str) -> tuple[int, ...] | None:
    out = run([binary, "--version"]).stdout.strip()
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", out)
    return tuple(int(part) for part in match.groups()) if match else None


def find_herdr() -> Path | None:
    """The Herdr to use: the person's own if new enough, wherever it is."""
    candidates = [paths()["herdr_bin"], shutil.which("herdr"), "/opt/homebrew/bin/herdr", "/usr/local/bin/herdr"]
    seen = set()
    for candidate in candidates:
        if not candidate or candidate in seen or not Path(candidate).exists():
            continue
        seen.add(candidate)
        version = herdr_version(str(candidate))
        if version and version >= HERDR_MIN:
            return Path(candidate)
    return None


def herdr() -> str:
    found = find_herdr()
    return str(found or paths()["herdr_bin"])


def brew() -> str | None:
    for candidate in ("/opt/homebrew/bin/brew", "/usr/local/bin/brew"):
        if Path(candidate).exists():
            return candidate
    return shutil.which("brew")


# ---------------------------------------------------------------- the person's settings


def load_contract() -> dict[str, Any]:
    data = json.loads((KIT / "keymap/hyper-keymap.json").read_text(encoding="utf-8"))
    keymap.validate_keys(data["keys"])
    return data


def actions_list() -> list[tuple[str, str, str]]:
    return [
        (item["id"], item["herdr_key"].replace("ctrl+alt+cmd+", "hyper+"), ACTIONS_KO.get(item["id"], ""))
        for item in load_contract()["keys"]
        if item["id"] not in keymap.FIXED_ACTIONS
    ]


def read_settings() -> dict[str, Any]:
    path = paths()["settings"]
    if not path.exists():
        raise Fail(f"{path}가 없습니다. `terminal-setting install`을 먼저 실행하세요")
    try:
        return personal.loads(path.read_text(encoding="utf-8"))
    except personal.SettingError as error:
        raise Fail(f"{path}: {error}") from None


def write_settings(data: dict[str, Any]) -> None:
    write_atomic(paths()["settings"], personal.dumps(data, actions_list()))


def load_settings() -> dict[str, Any]:
    data = read_settings()
    path = paths()["settings"]
    hyper = data.get("hyper", "caps_lock")
    if hyper not in keymap.HYPER_SOURCES:
        raise Fail(f"{path}: hyper = {hyper!r}: \"caps_lock\" 또는 \"right_option\"만 씁니다")
    tap = data.get("tap_switches_input", False)
    if not isinstance(tap, bool):
        raise Fail(f"{path}: tap_switches_input은 true 또는 false입니다")
    try:
        contract = keymap.apply_overrides(load_contract(), data.get("keys", {}))
    except keymap.ContractError as error:
        raise Fail(f"{path}: {error}") from None
    return {"hyper": hyper, "tap": tap, "contract": contract, "data": data}


# ---------------------------------------------------------------- rendering


def herdr_command() -> str:
    # Ghostty opened from the Dock has only /usr/bin:/bin:/usr/sbin:/sbin, and
    # Herdr's key commands and plugins inherit it; give them Homebrew and
    # ~/.local/bin (jq, yazi, go, terminal-setting).
    local_bin = home() / ".local/bin"
    path = f"{local_bin}:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    return f"/usr/bin/env PATH={path} {herdr()}"


INCLUDE_LOCAL = "config-file = ?local"


def render_ghostty(theme: str, contract: dict[str, Any], data: dict[str, Any] | None = None) -> str:
    template = (KIT / "templates/ghostty.config").read_text(encoding="utf-8")
    text = template.replace("{{THEME}}", theme).replace("{{HERDR}}", herdr_command())
    text = text.replace("{{KEYS}}", keymap.render_ghostty(contract).rstrip("\n"))
    mine = personal.ghostty_lines(data or {})
    if mine:
        block = "# 내 설정(~/.config/terminal-setting/settings.toml [ghostty])\n" + "\n".join(mine) + "\n\n"
        text = text.replace(INCLUDE_LOCAL, block + INCLUDE_LOCAL, 1)
    return text


def render_herdr(theme: str, contract: dict[str, Any], data: dict[str, Any] | None = None) -> str:
    template = (KIT / "themes" / theme / "herdr.toml").read_text(encoding="utf-8")
    block = keymap.drop_disabled(keymap.render_herdr(contract, keymap.KIT))
    text = template.replace("{{KEYS}}", block.rstrip("\n"))
    try:
        text = personal.apply_herdr(text, data or {})
    except (personal.SettingError, tomllib.TOMLDecodeError) as error:
        raise Fail(f"Herdr 설정: {error}") from None
    return text


def current_theme(state: dict[str, Any]) -> str:
    names = themes()
    if not names:
        raise Fail(f"{KIT}/themes에 테마가 없습니다. kit을 다시 받으세요(`terminal-setting update`)")
    theme = state.get("theme")
    return theme if theme in names else names[0]


# ---------------------------------------------------------------- pieces of install / apply


def carry_hand_edits(state: dict[str, Any]) -> list[str]:
    """Move what the person changed by hand in a kit file into their own files,
    so the rewrite that follows keeps it."""
    p = paths()
    notes = []
    ghostty, herdr_file = p["ghostty"], p["herdr"]
    old_ghostty = p["rendered"] / "ghostty"
    if ghostty.exists() and old_ghostty.exists() and not ghostty.is_symlink():
        current = ghostty.read_text(encoding="utf-8", errors="replace")
        if state["files"].get(str(ghostty)) not in (None, digest(current)):
            lines = personal.ghostty_hand_lines(current, old_ghostty.read_text(encoding="utf-8"))
            if lines:
                local = p["ghostty_local"]
                before = local.read_text(encoding="utf-8") if local.exists() else ""
                stamp = datetime.now().strftime("%Y-%m-%d")
                write_atomic(local, before.rstrip("\n") + f"\n\n# {stamp} Ghostty 설정 파일에서 손으로 고친 것을 옮겨 옴\n" + "\n".join(lines) + "\n")
                notes.append(f"Ghostty 설정을 손으로 고친 {len(lines)}줄을 {local}로 옮겨 그대로 씁니다")
    old_herdr = p["rendered"] / "herdr.toml"
    if herdr_file.exists() and old_herdr.exists() and not herdr_file.is_symlink():
        current = herdr_file.read_text(encoding="utf-8", errors="replace")
        if state["files"].get(str(herdr_file)) not in (None, digest(current)):
            moved, other = personal.herdr_hand_values(current, old_herdr.read_text(encoding="utf-8"))
            if moved:
                data = read_settings()
                data["herdr"].update(moved)
                write_settings(data)
                notes.append(f"Herdr 설정을 손으로 바꾼 것({', '.join(moved)})을 내 설정 파일로 옮겨 그대로 씁니다")
            if other:
                notes.append("Herdr 단축키·테마·목록을 손으로 바꾼 것은 옮기지 못해 백업만 했습니다. 단축키는 `terminal-setting key`로 바꿉니다")
    return notes


def apply_configs(state: dict[str, Any], *, reload: bool = True) -> list[str]:
    p = paths()
    notes = carry_hand_edits(state)
    settings = load_settings()
    theme = current_theme(state)
    contract = settings["contract"]
    data = settings["data"]
    ghostty_text = render_ghostty(theme, contract, data)
    herdr_text = render_herdr(theme, contract, data)
    for name in themes():
        write_owned(p["ghostty_themes"] / name, (KIT / "themes" / name / "ghostty-theme").read_text(encoding="utf-8"), state)
    write_owned(p["ghostty"], ghostty_text, state)
    if not p["ghostty_local"].exists():
        write_atomic(p["ghostty_local"], "# 내 Ghostty 설정. 여기에 쓴 것은 kit 업데이트가 건드리지 않고, 기본 설정 위에 덮어씁니다.\n# 흔한 것은 `terminal-setting set font-size 18`처럼 바꾸는 게 쉽습니다(`terminal-setting settings`).\n")
    write_owned(p["herdr"], herdr_text, state)
    write_atomic(p["rendered"] / "ghostty", ghostty_text)
    write_atomic(p["rendered"] / "herdr.toml", herdr_text)
    write_owned(p["auto_title"], (KIT / "herdr/auto-title.env").read_text(encoding="utf-8"), state)
    claude_theme = KIT / "themes" / theme / "claude-theme.json"
    if claude_theme.exists():
        write_owned(p["claude_theme"], claude_theme.read_text(encoding="utf-8"), state)
    notes += apply_claude_settings(state, data)
    notes += apply_karabiner(state, settings["hyper"], settings["tap"])
    notes += apply_input_hotkey(state, settings["tap"])
    state["theme"] = theme
    if reload:
        notes += reload_apps()
    return notes


def apply_karabiner(state: dict[str, Any], hyper: str, tap: bool) -> list[str]:
    path = paths()["karabiner"]
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if str(path) not in state["originals"]:
            state["originals"][str(path)] = str(backup(path, state, "설치 전 Karabiner 설정 보관"))
    else:
        data = {"profiles": [{"name": "Default profile", "selected": True, "complex_modifications": {"rules": []}, "virtual_hid_keyboard": {"keyboard_type_v2": "ansi"}}]}
        state["originals"].setdefault(str(path), "absent")
    profiles = data.setdefault("profiles", [])
    selected = [profile for profile in profiles if profile.get("selected")] or profiles[:1]
    if not selected:
        raise Fail(f"{path}에 Karabiner profile이 없습니다")
    rules = selected[0].setdefault("complex_modifications", {}).setdefault("rules", [])
    rules[:] = [rule for rule in rules if not rule.get("description", "").startswith(keymap.KIT_RULE_PREFIX)]
    notes = []
    for rule in rules:
        for manipulator in rule.get("manipulators", []):
            if manipulator.get("from", {}).get("key_code") == hyper:
                notes.append(f"주의: Karabiner 규칙 '{rule.get('description', '')}'도 {hyper}를 씁니다. terminal-setting 규칙이 먼저 적용됩니다")
    rules.insert(0, keymap.kit_hyper_rule(hyper, "f18" if tap else None))
    text = json.dumps(data, ensure_ascii=False, indent=4) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        write_atomic(path, text)
    return notes


def read_hotkey() -> dict[str, Any] | None:
    result = run(["defaults", "export", "com.apple.symbolichotkeys", "-"])
    if result.returncode != 0 or not result.stdout:
        return None
    data = plistlib.loads(result.stdout.encode("utf-8"))
    return data.get("AppleSymbolicHotKeys", {}).get(INPUT_HOTKEY_ID)


def write_hotkey(value: dict[str, Any]) -> None:
    xml = plistlib.dumps(value).decode("utf-8")
    body = xml[xml.index("<dict>"): xml.rindex("</dict>") + len("</dict>")]
    run(["defaults", "write", "com.apple.symbolichotkeys", "AppleSymbolicHotKeys", "-dict-add", INPUT_HOTKEY_ID, body], check=True)
    run(["/System/Library/PrivateFrameworks/SystemAdministration.framework/Resources/activateSettings", "-u"])


def apply_input_hotkey(state: dict[str, Any], tap: bool) -> list[str]:
    if not tap:
        return []
    current = read_hotkey()
    if current == INPUT_HOTKEY:
        return []
    state["ours"].setdefault("input_hotkey", {"before": current})
    write_hotkey(INPUT_HOTKEY)
    return ["한영 전환 단축키(입력 소스 다음으로)를 F18로 바꿨습니다. 한/A를 짧게 누르면 F18이 갑니다"]


def reload_apps() -> list[str]:
    notes = []
    script = 'tell application "Ghostty"\nif (count of terminals) > 0 then perform action "reload_config" on terminal 1\nend tell'
    if run(["pgrep", "-x", "ghostty"]).returncode == 0:
        if run(["osascript", "-e", script]).returncode != 0:
            notes.append("Ghostty: Cmd+Shift+, 를 눌러 설정을 다시 읽으세요")
    # `herdr status server` exits 0 also when no server runs; read its words.
    if "status: running" in run([herdr(), "status", "server"]).stdout:
        if run([herdr(), "server", "reload-config"]).returncode != 0:
            notes.append("Herdr: Hyper+R로 설정을 다시 읽으세요")
    return notes


# Claude settings the kit fills when the person has not set them (대표 2026-10-22):
# run without permission prompts, notify through Ghostty, the i-have-adhd reply
# style. Each is the person's to switch off (settings.toml), and uninstall
# removes only what the kit put there.
def claude_wanted(data: dict[str, Any]) -> dict[tuple[str, ...], Any]:
    wanted: dict[tuple[str, ...], Any] = {
        ("preferredNotifChannel",): "ghostty",
        ("inputNeededNotifEnabled",): True,
    }
    if data.get("claude_auto_approve", True):
        wanted[("permissions", "defaultMode")] = "bypassPermissions"
        wanted[("skipDangerousModePermissionPrompt",)] = True
    if data.get("claude_reply_style", "i-have-adhd") == "i-have-adhd":
        wanted[("outputStyle",)] = "i-have-adhd"
    return wanted


def get_path(tree: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if not isinstance(tree, dict) or key not in tree:
            return None
        tree = tree[key]
    return tree


def set_path(tree: dict[str, Any], keys: tuple[str, ...], value: Any) -> None:
    for key in keys[:-1]:
        tree = tree.setdefault(key, {})
    tree[keys[-1]] = value


def pop_path(tree: dict[str, Any], keys: tuple[str, ...]) -> None:
    parents = []
    for key in keys[:-1]:
        if not isinstance(tree.get(key), dict):
            return
        parents.append((tree, key))
        tree = tree[key]
    tree.pop(keys[-1], None)
    for parent, key in reversed(parents):
        if parent[key] == {}:
            parent.pop(key)


def apply_claude_settings(state: dict[str, Any], data: dict[str, Any]) -> list[str]:
    p = paths()
    p["claude_dir"].mkdir(parents=True, exist_ok=True)
    if not p["claude_settings"].exists():
        state["ours"]["claude_settings_created"] = True
    settings = json.loads(p["claude_settings"].read_text(encoding="utf-8")) if p["claude_settings"].exists() else {}
    before = json.dumps(settings, sort_keys=True)
    ours = {tuple(key) for key in state["ours"].get("claude_keys", [])}
    wanted = claude_wanted(data)
    notes = []
    for keys in list(ours):
        if keys not in wanted:
            pop_path(settings, keys)
            ours.discard(keys)
    for keys, value in wanted.items():
        current = get_path(settings, keys)
        if keys in ours or current is None:
            set_path(settings, keys, value)
            ours.add(keys)
        elif current != value and keys == ("permissions", "defaultMode"):
            notes.append(f"Claude 권한 방식은 쓰던 것({current})을 그대로 둡니다")
    if wanted.get(("outputStyle",)) == "i-have-adhd":
        write_owned(p["reply_style"], (KIT / "claude/output-styles/i-have-adhd.md").read_text(encoding="utf-8"), state)
    state["ours"]["claude_keys"] = sorted(list(keys) for keys in ours)
    if json.dumps(settings, sort_keys=True) != before:
        if p["claude_settings"].exists() and str(p["claude_settings"]) not in state["originals"]:
            state["originals"][str(p["claude_settings"])] = str(backup(p["claude_settings"], state, "설치 전 Claude 설정 보관"))
        write_atomic(p["claude_settings"], json.dumps(settings, ensure_ascii=False, indent=2) + "\n")
    return notes


def install_claude_parts(state: dict[str, Any]) -> list[str]:
    p = paths()
    notes = []
    p["claude_dir"].mkdir(parents=True, exist_ok=True)
    write_owned(p["statusline"], (KIT / "claude/statusline.sh").read_text(encoding="utf-8"), state, 0o755)
    if not p["claude_settings"].exists():
        state["ours"]["claude_settings_created"] = True
    settings = json.loads(p["claude_settings"].read_text(encoding="utf-8")) if p["claude_settings"].exists() else {}
    changed = False
    if "statusLine" not in settings:
        settings["statusLine"] = {"type": "command", "command": 'bash "$HOME/.claude/terminal-setting/statusline.sh"', "refreshInterval": 60}
        state["ours"]["statusLine"] = True
        changed = True
    elif not state["ours"].get("statusLine"):
        notes.append("Claude 상태 줄은 쓰던 것을 그대로 둡니다(terminal-setting 상태 줄: ~/.claude/terminal-setting/statusline.sh)")
    if settings.get("theme") in (None, CLAUDE_THEME):
        if settings.get("theme") != CLAUDE_THEME:
            settings["theme"] = CLAUDE_THEME
            state["ours"]["theme"] = True
            changed = True
    if changed:
        if p["claude_settings"].exists() and str(p["claude_settings"]) not in state["originals"]:
            state["originals"][str(p["claude_settings"])] = str(backup(p["claude_settings"], state, "설치 전 Claude 설정 보관"))
        write_atomic(p["claude_settings"], json.dumps(settings, ensure_ascii=False, indent=2) + "\n")
    p["skill"].parent.mkdir(parents=True, exist_ok=True)
    if p["skill"].is_symlink() or not p["skill"].exists():
        if p["skill"].is_symlink():
            p["skill"].unlink()
        p["skill"].symlink_to(KIT / "skill/terminal-setting")
    if not p["herdr_skill"].exists():
        result = run([herdr(), "--skill"])
        if result.returncode == 0 and result.stdout.startswith("---"):
            write_owned(p["herdr_skill"], result.stdout, state)
            state["ours"]["herdr_skill"] = True
    result = run([herdr(), "integration", "install", "claude"])
    if result.returncode != 0:
        notes.append(f"Herdr의 Claude 연결 실패: {(result.stderr or result.stdout).strip()[-200:]}")
    return notes


def install_plugins() -> list[str]:
    notes = []
    listed = run([herdr(), "plugin", "list"]).stdout
    for name in LOCAL_PLUGINS:
        root = KIT / "plugins" / name
        if str(root) in listed:
            continue
        result = run([herdr(), "plugin", "link", str(root)])
        if result.returncode != 0:
            notes.append(f"plugin {name} 연결 실패: {(result.stderr or result.stdout).strip()[-200:]}")
    if "herdr.auto-title" not in listed:
        repo, ref = AUTO_TITLE
        result = run([herdr(), "plugin", "install", repo, "--ref", ref, "--yes"])
        if result.returncode != 0:
            notes.append(f"auto-title plugin 설치 실패: {(result.stderr or result.stdout).strip()[-200:]}")
    return notes


def profile_files() -> list[Path]:
    # zsh is the macOS default; a bash login shell reads .bash_profile instead.
    files = [paths()["zprofile"]]
    if Path(os.environ.get("SHELL", "")).name == "bash":
        files.append(home() / ".bash_profile")
    return files


def ensure_profile(state: dict[str, Any]) -> None:
    for path in profile_files():
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if PROFILE_BEGIN in text:
            continue
        lines = [PROFILE_BEGIN]
        found = brew()
        if found and "brew shellenv" not in text:
            lines.append(f'eval "$({found} shellenv)"')
        lines.append('export PATH="$HOME/.local/bin:$PATH"')
        lines.append(PROFILE_END)
        write_atomic(path, text + ("\n" if text and not text.endswith("\n") else "") + "\n".join(lines) + "\n")
        state["ours"].setdefault("profiles", []).append(str(path))
        state["ours"]["zprofile"] = True


# An app the person installed without Homebrew (a downloaded dmg) makes
# `brew install --cask` stop with "already an App at …"; keep theirs.
CASK_PRESENT = {
    "ghostty": ["/Applications/Ghostty.app"],
    "karabiner-elements": ["/Applications/Karabiner-Elements.app"],
    "font-geist-mono": ["~/Library/Fonts/GeistMono*", "/Library/Fonts/GeistMono*"],
}


def cask_present(token: str) -> bool:
    for pattern in CASK_PRESENT.get(token, []):
        path = Path(pattern.replace("~", str(home()), 1))
        if any(path.parent.glob(path.name)):
            return True
    return False


def brewfile_for_this_mac() -> Path:
    lines = []
    for line in (KIT / "Brewfile").read_text(encoding="utf-8").splitlines():
        match = re.match(r'cask "([^"]+)"', line)
        if match and cask_present(match.group(1)):
            print(f"  · {match.group(1)}: 이미 있어 그대로 씁니다")
            continue
        lines.append(line)
    path = paths()["state"].with_name("Brewfile")
    write_atomic(path, "\n".join(lines) + "\n")
    return path


def confirm_or_fail(question: str, yes: bool) -> bool:
    """Ask on a terminal; without one (a Claude session) require --yes."""
    if yes:
        return True
    if not sys.stdin.isatty():
        raise Fail("확인할 화면이 없어 하지 않았습니다. 사용자에게 물어 '응'을 받은 뒤 --yes를 붙여 다시 실행합니다")
    return ask_yes(question, default=False)


def ask_yes(question: str, default: bool = True) -> bool:
    mark = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"{question} {mark} ").strip().lower()
    except EOFError:
        return default
    if not answer:
        return default
    return answer[0] in ("y", "ㅛ", "예", "네", "응")


def wait_enter(message: str) -> None:
    try:
        input(f"{message} (끝나면 Enter) ")
    except EOFError:
        pass


# ---------------------------------------------------------------- commands


def cmd_install(args: argparse.Namespace) -> int:
    p = paths()
    state = load_state()
    step = lambda n, text: print(f"\n[{n}/6] {text}")  # noqa: E731
    if not args.no_apps:
        step(1, "앱 설치(Ghostty·Karabiner·글꼴·도구). 처음이면 몇 분 걸립니다")
        found = brew()
        if not found:
            raise Fail("Homebrew가 없습니다. 설치 명령(install.sh)부터 다시 실행하세요")
        brewfile = brewfile_for_this_mac()
        if run_shown([found, "bundle", "--file", str(brewfile)]) != 0:
            raise Fail("앱 설치(brew bundle)가 실패했습니다. 인터넷을 확인하고 `terminal-setting install`을 다시 실행하세요")
        if find_herdr() is None:
            older = shutil.which("herdr")
            if older:
                print(f"  · 쓰던 Herdr({older})가 kit이 시험한 판보다 오래돼 새 판을 ~/.local/bin에 따로 깝니다. 쓰던 Herdr 창은 닫았다 열어야 새 판이 됩니다")
            if run_shown(["/bin/sh", "-c", "curl -fsSL https://herdr.dev/install.sh | sh"]) != 0:
                raise Fail("Herdr 설치가 실패했습니다. `terminal-setting install`을 다시 실행하세요")
        if not shutil.which("claude") and not (home() / ".local/bin/claude").exists():
            if run_shown(["/bin/bash", "-c", "curl -fsSL https://claude.ai/install.sh | bash"]) != 0:
                raise Fail("Claude Code 설치가 실패했습니다. `terminal-setting install`을 다시 실행하세요")
    ensure_profile(state)
    step(2, "내 키 설정")
    if not p["settings"].exists():
        if args.tap is None:
            tap = ask_yes("지금 한/A 키로 한영을 바꾸세요?")
        else:
            tap = args.tap == "yes"
        data = personal.empty()
        data["tap_switches_input"] = tap
        write_settings(data)
        print(f"  {p['settings']}에 적었습니다. 단축키·글자 크기 등은 나중에 `terminal-setting customize`로 언제든 바꿉니다")
    else:
        print(f"  쓰던 {p['settings']}를 그대로 씁니다")
    step(3, "Ghostty·Herdr·Karabiner 설정")
    notes = apply_configs(state, reload=not args.no_apps)
    save_state(state)
    step(4, "Herdr plugin·Claude 연결")
    if not args.no_apps:
        notes += install_plugins()
    notes += install_claude_parts(state)
    save_state(state)
    step(5, "권한 허용(Karabiner)")
    if not args.no_apps:
        if not karabiner_driver_ok():
            run(["open", "-a", "Karabiner-Elements"])
            print("  Karabiner-Elements 창이 열립니다. 창에 나오는 안내를 위에서부터 하나씩 따라 허용하세요.")
            print("  (백그라운드 서비스, 손쉬운 사용, 입력 모니터링, 드라이버 확장 프로그램. 창의 버튼이 맞는 시스템 설정 화면을 엽니다)")
            print("  마지막에 키보드 종류를 물으면 쓰는 키보드와 같은 것을 고릅니다(Apple 한국어 키보드는 보통 ANSI).")
            wait_enter("  허용을 마쳤으면")
        else:
            print("  이미 허용되어 있습니다")
    step(6, "점검")
    state.pop("_stamp", None)
    for note in state.pop("_notes", []) + notes:
        print(f"  · {note}")
    state["version"] = kit_version()
    save_state(state)
    ok = cmd_doctor(argparse.Namespace(quiet=True)) == 0
    print("\n설치가 끝났습니다." if ok else "\n설치는 끝났지만 위 ✘ 항목을 고쳐야 합니다. Claude에게 \"터미널 점검 결과 고쳐줘\"라고 하세요.")
    print_guide()
    if not args.no_apps:
        run(["open", "-a", "Ghostty"])
    return 0 if ok else 1


def guide_steps() -> list[str]:
    """What to try right after install, in order; each step names its fix."""
    try:
        settings = load_settings()
    except Fail:
        settings = {"hyper": "caps_lock", "tap": False}
    key = "한/A" if settings["hyper"] == "caps_lock" else "오른쪽 Option"
    steps = ["Ghostty(터미널 앱)가 열리고 그 안에 Herdr가 뜹니다. 왼쪽 사이드바가 보이면 됩니다. 안 열리면 Launchpad에서 Ghostty를 엽니다(처음엔 '열기'를 한 번 누름)."]
    if settings["tap"]:
        steps.append(f"{key}를 짧게 눌렀다 뗍니다: 한영이 바뀌면 됩니다. 1초 넘게 누르면 바뀌지 않는 게 정상입니다.")
    steps.append(f"{key}를 누른 채 ' (따옴표 키)를 누릅니다: 화면이 둘로 나뉘면 Hyper 키가 됩니다. 아무 일도 없으면 Karabiner-Elements 앱을 열어 남은 허용 안내가 있는지 보고, `terminal-setting env`의 ! 줄을 확인합니다.")
    if settings["hyper"] == "caps_lock":
        steps.append("Shift+한/A를 누릅니다: 대문자 고정이 켜지면 됩니다(다시 누르면 꺼짐).")
    steps.append("나뉜 칸 하나에 `claude`를 쓰고 Enter를 누릅니다. 브라우저가 열리면 로그인합니다(Claude Pro 이상 계정).")
    steps.append('Claude에게 첫 말: "terminal-setting 스킬로 이 터미널 환경 사용법을 처음 쓰는 사람에게 알려줘"')
    steps.append('막히면 터미널에 `terminal-setting doctor`, 또는 Claude에게 "터미널 점검해줘". 이 안내는 `terminal-setting guide`로 다시 봅니다.')
    return steps


def print_guide() -> None:
    print("\n이제 해 볼 것")
    for number, step in enumerate(guide_steps(), 1):
        print(f"  {number}. {step}")


def cmd_guide(args: argparse.Namespace) -> int:
    print_guide()
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    state = load_state()
    notes = apply_configs(state, reload=not args.no_reload)
    state.pop("_stamp", None)
    for note in state.pop("_notes", []) + notes:
        print(f"· {note}")
    save_state(state)
    print("적용했습니다. Karabiner(Hyper 키)는 바로, Ghostty·Herdr는 다시 읽은 뒤 바뀝니다.")
    return 0


def cmd_theme(args: argparse.Namespace) -> int:
    if isinstance(args.name, list):
        args.name = " ".join(args.name) or None
    state = load_state()
    names = themes()
    if args.name in (None, "list"):
        current = current_theme(state)
        for name in names:
            print(("● " if name == current else "  ") + name)
        return 0
    if args.name == "cycle":
        current = current_theme(state)
        target = names[(names.index(current) + 1) % len(names)]
    elif args.name in names:
        target = args.name
    else:
        raise Fail(f"없는 테마입니다: {args.name}. 있는 테마: {', '.join(names)}")
    state["theme"] = target
    notes = apply_configs(state)
    state.pop("_stamp", None)
    for note in state.pop("_notes", []) + notes:
        print(f"· {note}")
    save_state(state)
    print(f"테마: {target} (Claude는 새로 연 창부터 바뀝니다)")
    return 0


def cmd_keys(args: argparse.Namespace) -> int:
    settings = load_settings()
    by_id = {item["id"]: item["herdr_key"] for item in settings["contract"]["keys"]}
    rows = []
    for item in load_contract()["keys"]:
        chord = by_id.get(item["id"], "")
        rows.append({"action": item["id"], "key": friendly(chord), "chord": chord, "ko": ACTIONS_KO.get(item["id"], "")})
    if args.json:
        print(json.dumps({"hyper": settings["hyper"], "tap_switches_input": settings["tap"], "keys": rows}, ensure_ascii=False, indent=2))
        return 0
    source = keymap.HYPER_SOURCES[settings["hyper"]]
    print(f"Hyper 키: {source}" + (" (혼자 누르면 한영 전환)" if settings["tap"] else ""))
    for row in rows:
        print(f"  {row['key']:<20} {row['ko']}  [{row['action']}]")
    print("\n바꾸려면 `terminal-setting key 동작 hyper+키` (예: terminal-setting key theme_toggle hyper+y), 끄려면 off, 되돌리려면 default")
    return 0


# ---------------------------------------------------------------- changing the person's settings


def change(edit: Callable[[dict[str, Any]], str], *, reload: bool = True) -> int:
    """Edit settings.toml, apply, and put the old file back if applying fails."""
    path = paths()["settings"]
    before = path.read_text(encoding="utf-8") if path.exists() else None
    data = read_settings()
    try:
        message = edit(data)
        write_settings(data)
        state = load_state()
        notes = apply_configs(state, reload=reload)
    except (Fail, personal.SettingError, keymap.ContractError) as error:
        if before is not None:
            write_atomic(path, before)
        raise Fail(f"{error} (바꾸지 않았습니다)") from None
    state.pop("_stamp", None)
    for note in state.pop("_notes", []) + notes:
        print(f"· {note}")
    save_state(state)
    print(message)
    return 0


KEY_LABELS = {
    "quote": "'", "semicolon": ";", "minus": "-", "period": ".", "comma": ",",
    "left": "←", "right": "→", "up": "↑", "down": "↓",
    "space": "Space", "tab": "Tab", "enter": "Enter",
}


def friendly(chord: str) -> str:
    """ctrl+alt+cmd+quote -> Hyper+'; cmd+left -> Cmd+←."""
    if not chord:
        return "(끔)"
    for prefix, label in (("ctrl+alt+cmd+", "Hyper+"), ("hyper+", "Hyper+"), ("cmd+", "Cmd+")):
        if chord.startswith(prefix):
            key = chord[len(prefix):]
            return label + KEY_LABELS.get(key, key.upper() if len(key) == 1 else key)
    return chord


def shown(value: Any) -> str:
    if isinstance(value, bool):
        return "켬" if value else "끔"
    return str(value)


def cmd_set(args: argparse.Namespace) -> int:
    def edit(data: dict[str, Any]) -> str:
        value = personal.set_value(data, args.name, " ".join(args.value))
        return f"{args.name} = {shown(value)}: 적용했습니다"
    return change(edit, reload=not args.no_reload)


def cmd_unset(args: argparse.Namespace) -> int:
    def edit(data: dict[str, Any]) -> str:
        found = personal.unset_value(data, args.name)
        return f"{args.name}: 기본값으로 되돌렸습니다" if found else f"{args.name}: 이미 기본값입니다"
    return change(edit, reload=not args.no_reload)


def cmd_key(args: argparse.Namespace) -> int:
    known = {action for action, _, _ in actions_list()}
    if args.action not in known:
        raise Fail(f"{args.action!r}: 없는 동작입니다. `terminal-setting keys`의 대괄호 안 이름을 씁니다")

    def edit(data: dict[str, Any]) -> str:
        chord = args.chord.strip().lower()
        if chord in ("default", "기본", "기본값"):
            data["keys"].pop(args.action, None)
            return f"{args.action}: 기본 키로 되돌렸습니다"
        if chord in ("off", "끔", "끄기", "none"):
            data["keys"][args.action] = ""
            return f"{args.action}: 단축키를 껐습니다"
        keymap.parse_chord(chord)
        data["keys"][args.action] = chord
        return f"{args.action} = {chord}: 적용했습니다"
    return change(edit, reload=not args.no_reload)


def cmd_reset(args: argparse.Namespace) -> int:
    if not confirm_or_fail("바꾼 단축키·모양·Herdr 설정을 모두 기본값으로 되돌릴까요? (Hyper 키·한영 설정은 그대로)", args.yes):
        return 1

    def edit(data: dict[str, Any]) -> str:
        data["keys"], data["ghostty"], data["herdr"] = {}, {}, {}
        return "기본값으로 되돌렸습니다"
    return change(edit)


def cmd_settings(args: argparse.Namespace) -> int:
    data = read_settings()
    print(f"내 설정 파일: {paths()['settings']}\n")
    for name, setting in personal.LOOK.items():
        value = personal.current_value(data, name)
        mark = "●" if value is not None and setting.where != "top" else " "
        now = shown(value) if value is not None else f"기본({setting.default})"
        print(f"  {mark} {name:<14} {now:<16} {setting.ko}")
    others = [(f"ghostty.{k}", v) for k, v in data["ghostty"].items() if k not in {s.key for s in personal.LOOK.values() if s.where == "ghostty"}]
    others += [(f"herdr.{k}", v) for k, v in data["herdr"].items() if k not in {s.key for s in personal.LOOK.values() if s.where == "herdr"}]
    for name, value in others:
        print(f"  ● {name:<14} {shown(value)}")
    if data["keys"]:
        print("\n  바꾼 단축키:")
        for action, chord in data["keys"].items():
            print(f"    {friendly(chord):<12} {ACTIONS_KO.get(action, '')}  [{action}]")
    local = paths()["ghostty_local"]
    lines = [l for l in local.read_text(encoding="utf-8").splitlines() if l.strip() and not l.lstrip().startswith("#")] if local.exists() else []
    if lines:
        print(f"\n  {local}: {len(lines)}줄")
    print("\n바꾸기: `terminal-setting set 이름 값` · 되돌리기: `terminal-setting unset 이름` · 메뉴: `terminal-setting customize`")
    return 0


def cmd_customize(args: argparse.Namespace) -> int:
    """A numbered menu for people who would rather not type commands."""
    names = list(personal.LOOK)
    while True:
        data = read_settings()
        print("\nterminal-setting 꾸미기 (번호를 고르고 Enter, 끝내려면 q)")
        for number, name in enumerate(names, 1):
            setting = personal.LOOK[name]
            value = personal.current_value(data, name)
            now = shown(value) if value is not None else f"기본({setting.default})"
            print(f"  {number:>2}. {setting.ko}: {now}")
        print("   k. 단축키 바꾸기")
        print("   t. 테마 바꾸기")
        print("   r. 모두 기본값으로")
        try:
            choice = input("> ").strip().lower()
        except EOFError:
            return 0
        if choice in ("q", "", "ㅂ"):
            return 0
        try:
            if choice in ("k", "ㅏ"):
                for number, (action, default, ko) in enumerate(actions_list(), 1):
                    now = friendly(data["keys"].get(action, default))
                    print(f"  {number:>2}. {ko}: {now}")
                picked = input("바꿀 번호 > ").strip()
                action = actions_list()[int(picked) - 1][0]
                chord = input("새 키(예: hyper+y, cmd+k, 끄려면 off, 되돌리려면 default) > ").strip()
                cmd_key(argparse.Namespace(action=action, chord=chord, no_reload=False))
            elif choice in ("t", "ㅅ"):
                for number, name in enumerate(themes(), 1):
                    print(f"  {number}. {name}")
                picked = input("테마 번호 > ").strip()
                cmd_theme(argparse.Namespace(name=themes()[int(picked) - 1]))
            elif choice in ("r", "ㄱ"):
                cmd_reset(argparse.Namespace(yes=False))
            else:
                name = names[int(choice) - 1]
                setting = personal.LOOK[name]
                options = getattr(setting.parse, "options", None)
                if options:
                    for number, option in enumerate(options, 1):
                        print(f"  {number}. {shown(option == 'on') if options == ('on', 'off') else option}")
                    raw = input("번호(기본값으로 되돌리려면 default) > ").strip()
                    if raw.isdigit() and 1 <= int(raw) <= len(options):
                        raw = options[int(raw) - 1]
                else:
                    hint = getattr(setting.parse, "hint", "")
                    raw = input(f"{setting.ko} 새 값{f'({hint})' if hint else ''}, 되돌리려면 default > ").strip()
                if raw.lower() in ("default", "기본", "기본값"):
                    cmd_unset(argparse.Namespace(name=name, no_reload=False))
                else:
                    cmd_set(argparse.Namespace(name=name, value=[raw], no_reload=False))
        except (ValueError, IndexError):
            print("목록에 있는 번호를 고릅니다")
        except Fail as error:
            print(f"안 됐습니다: {error}")


# ---------------------------------------------------------------- this Mac's facts


KEY_TOOLS = ("Raycast", "BetterTouchTool", "Hammerspoon", "Keyboard Maestro Engine", "Alfred", "Rectangle")


def mac_facts() -> dict[str, Any]:
    """Read-only facts that decide how to fit the kit to this Mac."""
    facts: dict[str, Any] = {}
    facts["macos"] = run(["sw_vers", "-productVersion"]).stdout.strip()
    facts["chip"] = "Apple" if run(["uname", "-m"]).stdout.strip() == "arm64" else "Intel"
    languages = re.findall(r'"?([A-Za-z]{2}(?:-[A-Za-z]+)*)"?,?\n', run(["defaults", "read", "-g", "AppleLanguages"]).stdout)
    facts["ui_language"] = languages[0] if languages else ""
    facts["dark_mode"] = run(["defaults", "read", "-g", "AppleInterfaceStyle"]).stdout.strip() == "Dark"
    listing = run(["hidutil", "list", "--matching", '{"PrimaryUsagePage":1,"PrimaryUsage":6}']).stdout
    keyboards = []
    for line in listing.split("Devices:")[0].splitlines():
        match = re.search(r"^(0x[0-9a-f]+)\s+(0x[0-9a-f]+).*AppleHIDKeyboardEventDriver\S*\s+(.+?)\s+\(null\)\s+([01])\s*$", line)
        if match and "Karabiner" not in match.group(3):
            keyboards.append({
                "name": match.group(3).strip(),
                "built_in": match.group(4) == "1",
                "id": f"{int(match.group(1), 16)}-{int(match.group(2), 16)}",
            })
    facts["keyboards"] = keyboards
    sources = run(["defaults", "read", "com.apple.HIToolbox", "AppleEnabledInputSources"]).stdout
    names = re.findall(r'"KeyboardLayout Name" = "?([^";]+)"?;', sources)
    names += [mode.rsplit(".", 1)[-1] for mode in re.findall(r'"Input Mode" = "([^"]+)"', sources)]
    facts["input_sources"] = names
    running = run(["ps", "-axo", "comm"]).stdout
    facts["key_tools_running"] = [tool for tool in KEY_TOOLS if f"/{tool}.app/" in running]
    raycast = home() / "Library/Preferences/com.raycast.macos.plist"
    hyper_state = None
    if raycast.exists():
        try:
            state = plistlib.loads(raycast.read_bytes()).get("raycast_hyperKey_state")
            hyper_state = state.get("enabled") if isinstance(state, dict) else None
        except Exception:
            hyper_state = None
    facts["raycast_hyper_key"] = hyper_state
    keyboard_type = None
    karabiner = paths()["karabiner"]
    if karabiner.exists():
        try:
            data = json.loads(karabiner.read_text(encoding="utf-8"))
            selected = [p for p in data.get("profiles", []) if p.get("selected")] or data.get("profiles", [])[:1]
            keyboard_type = selected[0].get("virtual_hid_keyboard", {}).get("keyboard_type_v2") if selected else None
        except (json.JSONDecodeError, IndexError):
            keyboard_type = None
    facts["karabiner_keyboard_type"] = keyboard_type
    # macOS's own modifier-key settings are ignored while Karabiner runs; a
    # Simple Modification on the Hyper key in Karabiner comes before the kit's
    # rule and blocks it.
    blocked = []
    if karabiner.exists():
        try:
            for profile in json.loads(karabiner.read_text(encoding="utf-8")).get("profiles", []):
                if not profile.get("selected"):
                    continue
                mods = list(profile.get("simple_modifications", []))
                for device in profile.get("devices", []):
                    mods += device.get("simple_modifications", [])
                for mod in mods:
                    key = mod.get("from", {}).get("key_code")
                    if key in keymap.HYPER_SOURCES:
                        blocked.append(key)
        except (json.JSONDecodeError, AttributeError):
            pass
    facts["karabiner_simple_blocks_hyper"] = sorted(set(blocked))
    found = find_herdr()
    facts["herdr"] = run([str(found), "--version"]).stdout.strip() if found else None
    return facts


def cmd_env(args: argparse.Namespace) -> int:
    facts = mac_facts()
    if args.json:
        print(json.dumps(facts, ensure_ascii=False, indent=2))
        return 0
    print(f"macOS {facts['macos']} · {facts['chip']} 칩 · 화면 언어 {facts['ui_language'] or '?'} · {'다크' if facts['dark_mode'] else '라이트'} 모드")
    boards = ", ".join(f"{k['name']}{'(내장)' if k['built_in'] else ''}" for k in facts["keyboards"]) or "확인 못 함"
    print(f"키보드: {boards}")
    print(f"입력 소스 {len(facts['input_sources'])}개: {', '.join(facts['input_sources']) or '확인 못 함'}")
    print(f"Karabiner 키보드 종류: {facts['karabiner_keyboard_type'] or '아직 안 정함'}")
    print(f"Herdr: {facts['herdr'] or '없음'}")
    for warning in mac_warnings(facts):
        print(f"! {warning}")
    return 0


def mac_warnings(facts: dict[str, Any]) -> list[str]:
    warnings = []
    if facts["karabiner_simple_blocks_hyper"]:
        keys = ", ".join(keymap.HYPER_SOURCES[k] for k in facts["karabiner_simple_blocks_hyper"])
        warnings.append(f"Karabiner Simple Modifications에서 {keys}을(를) 다른 키로 바꿔 두었습니다. 그 줄이 먼저 적용돼 Hyper가 안 되니, 쓰지 않으면 그 줄을 지웁니다")
    if facts["raycast_hyper_key"]:
        warnings.append("Raycast의 Hyper Key가 켜져 있습니다. Karabiner의 Hyper와 겹치니 Raycast 설정 > Advanced > Hyper Key를 끕니다")
    others = [tool for tool in facts["key_tools_running"] if tool != "Raycast"]
    if others:
        warnings.append(f"키를 바꾸는 다른 앱이 돌고 있습니다: {', '.join(others)}. 단축키가 안 먹거나 겹치면 그 앱 설정부터 봅니다")
    if len(facts["input_sources"]) > 2:
        warnings.append("입력 소스가 셋 이상이라 한/A를 짧게 누르면 다음 입력 소스로 차례로 넘어갑니다")
    if any(not k["built_in"] for k in facts["keyboards"]):
        warnings.append("외장 키보드가 있습니다. Windows용 키보드면 Alt=Option, Windows 키=Command 자리이고, 기호가 다르게 찍히면 Karabiner > Virtual Keyboard에서 키보드 종류를 바꿉니다")
    return warnings


def karabiner_driver_ok() -> bool:
    result = run(["systemextensionsctl", "list"])
    return any("Karabiner" in line and "[activated enabled]" in line for line in result.stdout.splitlines())


def cmd_doctor(args: argparse.Namespace) -> int:
    p = paths()
    state = load_state()
    checks: list[tuple[bool, str, str]] = []

    def check(ok: bool, label: str, fix: str = "") -> None:
        checks.append((ok, label, fix))

    check(brew() is not None, "Homebrew", "install.sh를 다시 실행")
    check(Path("/Applications/Ghostty.app").exists(), "Ghostty 앱", "terminal-setting install")
    check(Path("/Applications/Karabiner-Elements.app").exists(), "Karabiner-Elements 앱", "terminal-setting install")
    found = find_herdr()
    check(found is not None, f"Herdr {'.'.join(map(str, HERDR_MIN))} 이상", "terminal-setting install (새 판을 ~/.local/bin에 깝니다)")
    if found is not None:
        version = run([herdr(), "--version"]).stdout.strip()
        result = run([herdr(), "config", "check"])
        check(result.returncode == 0 and "ok" in result.stdout, f"Herdr 설정 검사 ({version})", (result.stdout + result.stderr).strip()[-300:] or "terminal-setting apply")
        listed = run([herdr(), "plugin", "list"]).stdout
        missing = [pid for pid in PLUGIN_IDS if pid not in listed]
        check(not missing, "Herdr plugin 3개", f"빠진 것: {', '.join(missing)} → terminal-setting install")
        integration = run([herdr(), "integration", "status"]).stdout
        check(bool(re.search(r"(?m)^claude: current", integration)), "Herdr ↔ Claude 연결", "herdr integration install claude")
    try:
        settings = load_settings()
        check(True, f"내 설정 ({p['settings']})")
    except Fail as error:
        settings = None
        check(False, "내 설정", str(error))
    for key in ("ghostty", "herdr"):
        path = p[key]
        recorded = state["files"].get(str(path))
        same = path.exists() and recorded == digest(path.read_text(encoding="utf-8", errors="replace"))
        check(same, f"{path.name} 설정이 kit 것", "terminal-setting apply (손으로 고친 것은 백업됩니다)")
    alt = home() / ".config/ghostty/config.ghostty"
    check(not alt.exists(), "Ghostty 설정 파일이 하나", f"{alt}가 kit 설정을 덮을 수 있습니다. 내용을 ~/.config/ghostty/local로 옮기고 지우세요")
    if p["karabiner"].exists():
        data = json.loads(p["karabiner"].read_text(encoding="utf-8"))
        rules = [r.get("description", "") for prof in data.get("profiles", []) if prof.get("selected") for r in prof.get("complex_modifications", {}).get("rules", [])]
        check(any(r.startswith(keymap.KIT_RULE_PREFIX) for r in rules), "Karabiner Hyper 규칙", "terminal-setting apply")
    else:
        check(False, "Karabiner Hyper 규칙", "terminal-setting apply")
    check(karabiner_driver_ok(), "Karabiner 드라이버 허용", "Karabiner-Elements 앱을 열고 창의 허용 안내를 위에서부터 따라 하기(드라이버 확장 프로그램 포함)")
    if settings and settings["tap"]:
        check(read_hotkey() == INPUT_HOTKEY, "한영 전환 단축키 F18", "terminal-setting apply")
    check(bool(shutil.which("claude")) or (home() / ".local/bin/claude").exists(), "Claude Code", "terminal-setting install")
    check(p["skill"].exists(), "Claude terminal-setting 스킬", "terminal-setting install")
    on_path = str(home() / ".local/bin") in os.environ.get("PATH", "").split(":")
    check(on_path or PROFILE_BEGIN in (p["zprofile"].read_text(encoding="utf-8") if p["zprofile"].exists() else ""), "terminal-setting 명령 경로", "새 터미널 창을 엽니다")
    bad = 0
    for ok, label, fix in checks:
        if ok and getattr(args, "quiet", False):
            continue
        print(f"{'✔' if ok else '✘'} {label}" + ("" if ok else f"\n    → {fix}"))
        bad += not ok
    if getattr(args, "quiet", False) and not bad:
        print("  모든 점검 통과")
    print("  (입력 모니터링 허용은 macOS가 알려 주지 않아 점검하지 못합니다. Hyper 키가 안 먹으면 그 허용부터 확인합니다)")
    return 1 if bad else 0


def latest_tag() -> str:
    with urllib.request.urlopen(f"https://api.github.com/repos/{REPO}/tags", timeout=20) as response:
        tags = json.load(response)
    if not tags:
        raise Fail("올라온 판이 없습니다")
    return tags[0]["name"]


def cmd_update(args: argparse.Namespace) -> int:
    tag = args.ref or latest_tag()
    if tag == kit_version() and not args.ref:
        print(f"이미 최신입니다 ({tag}). 설정만 다시 적용합니다")
    else:
        url = f"https://codeload.github.com/{REPO}/tar.gz/refs/tags/{tag}"
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "kit.tar.gz"
            with urllib.request.urlopen(url, timeout=60) as response:
                archive.write_bytes(response.read())
            with tarfile.open(archive) as tar:
                tar.extractall(tmp, filter="data")
            unpacked = next(path for path in Path(tmp).iterdir() if path.is_dir())
            replace_kit(unpacked)
        print(f"kit을 {tag}로 바꿨습니다")
    # Run the new code for the rest of the update.
    os.execv(sys.executable, [sys.executable, "-I", str(KIT / "lib/terminal_setting.py"), "refresh"])


def cmd_refresh(args: argparse.Namespace) -> int:
    """After an update: settings, plugins and the Claude link from the new kit."""
    state = load_state()
    notes = apply_configs(state)
    notes += install_plugins()
    notes += install_claude_parts(state)
    state.pop("_stamp", None)
    for note in state.pop("_notes", []) + notes:
        print(f"· {note}")
    state["version"] = kit_version()
    save_state(state)
    ok = cmd_doctor(argparse.Namespace(quiet=True)) == 0
    print(f"terminal-setting-kit {kit_version()}: " + ("다 됐습니다" if ok else "위 ✘를 고칩니다(앱이 새로 필요하면 터미널에서 terminal-setting install)"))
    return 0 if ok else 1


def replace_kit(new_root: Path) -> None:
    old = KIT.with_name(KIT.name + ".old")
    if old.exists():
        shutil.rmtree(old)
    shutil.copytree(new_root, KIT.with_name(KIT.name + ".new"), symlinks=True)
    KIT.rename(old)
    KIT.with_name(KIT.name + ".new").rename(KIT)
    shutil.rmtree(old)


def restore(path: Path, original: str) -> None:
    if original == "absent":
        if path.exists() or path.is_symlink():
            path.unlink()
    elif Path(original).exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, path)


def prune_empty(folder: Path) -> None:
    """Remove folders the kit made and left empty, never the app roots."""
    stop = {home(), home() / ".config", home() / ".claude", home() / ".local", home() / ".local/share", home() / ".local/state"}
    while folder not in stop and folder.is_dir() and home() in folder.parents and not any(folder.iterdir()):
        folder.rmdir()
        folder = folder.parent


def cmd_uninstall(args: argparse.Namespace) -> int:
    p = paths()
    state = load_state()
    if not confirm_or_fail("terminal-setting 설정을 지우고 설치 전으로 되돌릴까요?", args.yes):
        return 1
    for pid in PLUGIN_IDS:
        run([herdr(), "plugin", "uninstall" if pid == "herdr.auto-title" else "unlink", pid])
    run([herdr(), "integration", "uninstall", "claude"])
    if p["karabiner"].exists():
        data = json.loads(p["karabiner"].read_text(encoding="utf-8"))
        for profile in data.get("profiles", []):
            rules = profile.get("complex_modifications", {}).get("rules", [])
            rules[:] = [r for r in rules if not r.get("description", "").startswith(keymap.KIT_RULE_PREFIX)]
        write_atomic(p["karabiner"], json.dumps(data, ensure_ascii=False, indent=4) + "\n")
    hotkey = state["ours"].get("input_hotkey")
    if hotkey:
        write_hotkey(hotkey.get("before") or INPUT_HOTKEY_DEFAULT)
    if p["claude_settings"].exists():
        settings = json.loads(p["claude_settings"].read_text(encoding="utf-8"))
        if state["ours"].get("statusLine"):
            settings.pop("statusLine", None)
        if state["ours"].get("theme") and settings.get("theme") == CLAUDE_THEME:
            settings.pop("theme", None)
        for keys in state["ours"].get("claude_keys", []):
            pop_path(settings, tuple(keys))
        leftover = {k: v for k, v in settings.items() if v not in ({}, [], None)}
        if state["ours"].get("claude_settings_created") and not leftover:
            p["claude_settings"].unlink()
        else:
            write_atomic(p["claude_settings"], json.dumps(settings, ensure_ascii=False, indent=2) + "\n")
    if p["skill"].is_symlink():
        p["skill"].unlink()
        prune_empty(p["skill"].parent)
    for key, original in state["originals"].items():
        path = Path(key)
        if path in (p["karabiner"], p["claude_settings"]):
            continue
        restore(path, original)
        if original == "absent":
            prune_empty(path.parent)
    for name in state["ours"].get("profiles", [str(p["zprofile"])] if state["ours"].get("zprofile") else []):
        profile = Path(name)
        if not profile.exists():
            continue
        text = profile.read_text(encoding="utf-8")
        text = re.sub(rf"\n?{re.escape(PROFILE_BEGIN)}.*?{re.escape(PROFILE_END)}\n?", "\n", text, flags=re.S)
        write_atomic(profile, text.strip("\n") + "\n" if text.strip() else "")
    reload_apps()
    if p["bin"].is_symlink():
        p["bin"].unlink()
    p["state"].unlink(missing_ok=True)
    print("되돌렸습니다. 남긴 것:")
    print(f"  · 내 설정 {p['settings']}, 내 Ghostty 설정 {p['ghostty_local']}, 백업 {p['backups']}")
    print("  · 앱: Ghostty·Karabiner-Elements·Geist Mono 글꼴(Homebrew 앱), Herdr(~/.local/bin/herdr), Claude Code(~/.local/bin/claude),")
    print("    도구 python@3.14·jq·yazi·go(Homebrew). 앱까지 지우려면: brew uninstall --cask ghostty karabiner-elements font-geist-mono")
    print("    (다른 데서도 쓸 수 있는 Homebrew 도구·Herdr·Claude는 남겨 둡니다)")
    if not args.keep_kit and KIT.name == "terminal-setting-kit":
        shutil.rmtree(KIT, ignore_errors=True)
    return 0


def cmd_move_pane_right(args: argparse.Namespace) -> int:
    os.execv(sys.executable, [sys.executable, "-I", str(KIT / "lib/move_pane_right.py"), *args.rest])


def cmd_render(args: argparse.Namespace) -> int:
    """Write each theme's Ghostty and Herdr config into a folder (for checks)."""
    out = Path(args.out)
    contract = load_contract()
    for theme in themes():
        target = out / theme
        target.mkdir(parents=True, exist_ok=True)
        (target / "ghostty.config").write_text(render_ghostty(theme, contract), encoding="utf-8")
        (target / "herdr.toml").write_text(render_herdr(theme, contract), encoding="utf-8")
    print(out)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="terminal-setting", description="terminal-setting-kit 터미널 환경 관리")
    parser.add_argument("--version", action="version", version=f"terminal-setting-kit {kit_version()}")
    sub = parser.add_subparsers(dest="command", required=True)
    install = sub.add_parser("install", help="설치하거나 끊긴 설치를 이어서 하기")
    install.add_argument("--tap", choices=("yes", "no"), help="한/A를 혼자 누르면 한영 전환(묻지 않고 정할 때)")
    install.add_argument("--no-apps", action="store_true", help="앱 설치·권한·플러그인 없이 설정만(시험용)")
    install.set_defaults(func=cmd_install)
    apply = sub.add_parser("apply", help="내 키 설정을 다시 적용")
    apply.add_argument("--no-reload", action="store_true")
    apply.set_defaults(func=cmd_apply)
    theme = sub.add_parser("theme", help="테마 보기·바꾸기: list | cycle | <이름>")
    theme.add_argument("name", nargs="*")
    theme.set_defaults(func=cmd_theme)
    for name, helptext in (("set", "설정 바꾸기: set 이름 값 (이름 목록: settings)"), ("unset", "설정을 기본값으로: unset 이름")):
        parser_ = sub.add_parser(name, help=helptext)
        parser_.add_argument("name")
        if name == "set":
            parser_.add_argument("value", nargs="+")
        parser_.add_argument("--no-reload", action="store_true")
        parser_.set_defaults(func=cmd_set if name == "set" else cmd_unset)
    key = sub.add_parser("key", help="단축키 바꾸기: key 동작 hyper+키 | off | default")
    key.add_argument("action")
    key.add_argument("chord")
    key.add_argument("--no-reload", action="store_true")
    key.set_defaults(func=cmd_key)
    settings_ = sub.add_parser("settings", help="내 설정 보기(바꿀 수 있는 이름과 지금 값)")
    settings_.set_defaults(func=cmd_settings)
    customize = sub.add_parser("customize", help="꾸미기 메뉴(번호로 고르기)")
    customize.set_defaults(func=cmd_customize)
    reset = sub.add_parser("reset", help="바꾼 것을 모두 기본값으로")
    reset.add_argument("--yes", action="store_true")
    reset.set_defaults(func=cmd_reset)
    keys = sub.add_parser("keys", help="단축키 표")
    keys.add_argument("--json", action="store_true")
    keys.set_defaults(func=cmd_keys)
    guide = sub.add_parser("guide", help="설치 뒤 해 볼 것(키 확인 순서)")
    guide.set_defaults(func=cmd_guide)
    env = sub.add_parser("env", help="이 Mac 정보(키보드·입력 소스·언어·겹치는 앱, 읽기만)")
    env.add_argument("--json", action="store_true")
    env.set_defaults(func=cmd_env)
    doctor = sub.add_parser("doctor", help="점검")
    doctor.set_defaults(func=cmd_doctor, quiet=False)
    update = sub.add_parser("update", help="새 판 받기")
    update.add_argument("--ref", help="판 이름(태그)")
    update.set_defaults(func=cmd_update)
    uninstall = sub.add_parser("uninstall", help="설치 전으로 되돌리기")
    uninstall.add_argument("--yes", action="store_true")
    uninstall.add_argument("--keep-kit", action="store_true")
    uninstall.set_defaults(func=cmd_uninstall)
    move = sub.add_parser("move-pane-right", help=argparse.SUPPRESS)
    move.add_argument("rest", nargs=argparse.REMAINDER)
    move.set_defaults(func=cmd_move_pane_right)
    refresh = sub.add_parser("refresh", help=argparse.SUPPRESS)
    refresh.set_defaults(func=cmd_refresh)
    render = sub.add_parser("render", help=argparse.SUPPRESS)
    render.add_argument("--out", required=True)
    render.set_defaults(func=cmd_render)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Fail as error:
        print(f"terminal-setting: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

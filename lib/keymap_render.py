#!/usr/bin/env python3.14
"""Render the Hyper key contract into Ghostty, Herdr and Karabiner text.

Pure functions with no paths of this Mac: sync_keymap.py uses them for this
Mac and terminal-setting-kit ships this file to render on the receiver's Mac.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple


GHOSTTY_BEGIN = "# BEGIN ghostty-herdr-tmux-keyboard-c HYPER bridge"
GHOSTTY_END = "# END ghostty-herdr-tmux-keyboard-c HYPER bridge"
HERDR_BEGIN = "# BEGIN ghostty-herdr-tmux-keyboard-c HYPER bindings"
HERDR_END = "# END ghostty-herdr-tmux-keyboard-c HYPER bindings"
HYPER_RULE = "Caps Lock -> Hyper (Ctrl+Option+Command); modifier only"


class ContractError(RuntimeError):
    pass


class Target(NamedTuple):
    """Where rendered key commands run: this Mac, or terminal-setting-kit on another Mac.

    The keys come from the one contract for both; only the commands behind them
    differ; the Caps Lock rule is `hyper_rule` (this Mac) or `kit_hyper_rule`.
    """

    name: str
    theme_cycle_command: str
    move_pane_command: str
    theme_names: tuple[str, ...]


KIT_CLI = '"$HOME/.local/bin/terminal-setting"'
KIT = Target(
    name="kit",
    theme_cycle_command=f"HERDR_ENV=1 {KIT_CLI} theme cycle",
    move_pane_command=f"{KIT_CLI} move-pane-right",
    theme_names=("Eyes Day", "fapibrown", "Eyes Night"),
)


def validate_keys(keys: list[dict[str, Any]]) -> None:
    ids = [item.get("id") for item in keys]
    sequences = [item.get("csi") for item in keys]
    triggers = [trigger for item in keys for trigger in item.get("ghostty_triggers", [])]
    for label, values in (("id", ids), ("CSI", sequences), ("trigger", triggers)):
        if len(values) != len(set(values)):
            raise ContractError(f"duplicate {label} in Hyper contract")
    for item in keys:
        csi = item["csi"]
        if ":1" not in csi or not csi.endswith(("u", "A", "B", "C", "D")):
            raise ContractError(f"{item['id']}: invalid explicit press CSI")
        input_class = item.get("input_class")
        expected_modifier = {"hyper": 15, "command": 9}.get(input_class)
        if expected_modifier is None:
            raise ContractError(f"{item['id']}: input_class must be hyper or command")
        if f";{expected_modifier}:1" not in csi:
            raise ContractError(
                f"{item['id']}: {input_class} must use Kitty modifier {expected_modifier}"
            )
        expected_trigger = (
            "ctrl+alt+super+" if input_class == "hyper" else "super+"
        )
        item_triggers = item.get("ghostty_triggers", [])
        if not item_triggers or any(
            not trigger.startswith(expected_trigger) for trigger in item_triggers
        ):
            raise ContractError(
                f"{item['id']}: {input_class} trigger must start with {expected_trigger}"
            )
        if any("shift" in trigger for trigger in item_triggers):
            raise ContractError(f"{item['id']}: Shift is forbidden in Hyper triggers")
        herdr_key = item.get("herdr_key")
        expected_herdr = (
            "ctrl+alt+cmd+" if input_class == "hyper" else "cmd+"
        )
        if herdr_key is not None and not herdr_key.startswith(expected_herdr):
            raise ContractError(
                f"{item['id']}: {input_class} Herdr key must start with {expected_herdr}"
            )


def key_lookup(contract: dict[str, Any]) -> dict[str, str]:
    return {
        item["id"]: item["herdr_key"]
        for item in contract["keys"]
        if item.get("herdr_key")
    }


def render_ghostty(contract: dict[str, Any]) -> str:
    lines = [
        GHOSTTY_BEGIN,
        "# Caps/한·A is Ctrl+Option+Command in Karabiner. Emit explicit",
        "# Kitty press events: Hyper stays modifier 15; Command stays modifier 9.",
        "# Herdr consumes the exact semantic event without a Shift layer.",
    ]
    for item in contract["keys"]:
        for trigger in item["ghostty_triggers"]:
            lines.append(f"keybind = {trigger}=csi:{item['csi']}")
    lines.extend([GHOSTTY_END, ""])
    return "\n".join(lines)


class _Lookup(dict):
    # A key the user turned off is absent from the contract; it renders as ""
    # and drop_disabled removes what Herdr cannot take empty.
    def __missing__(self, key: str) -> str:
        return ""


def render_herdr(contract: dict[str, Any], target: Target) -> str:
    k = _Lookup(key_lookup(contract))
    digits = k["tab_1"].removesuffix("1") + "1..9"
    return f"""{HERDR_BEGIN}
# F24 is an inert schema sentinel: Herdr requires a prefix value, but no action
# below uses the prefix table and no input layer emits F24.
[keys]
prefix = "f24"
help = "{k['help']}"
settings = "{k['settings']}"
detach = "{k['detach']}"
reload_config = "{k['reload']}"
open_notification_target = "{k['notification_target']}"

workspace_picker = "{k['workspace_picker']}"
goto = "{k['goto_or_window_tree']}"
new_workspace = ""  # {k['workspace_new']} is a [[keys.command]]: new workspace in $HOME
new_worktree = "{k['worktree_new']}"
open_worktree = ""
remove_worktree = ""
rename_workspace = "{k['workspace_rename']}"
close_workspace = "{k['workspace_close']}"
previous_workspace = "{k['workspace_previous']}"
next_workspace = "{k['workspace_next']}"
previous_agent = ["{k['agent_previous_or_pane_up']}", "{k['agent_previous_alias']}"]
next_agent = "{k['agent_next_or_pane_down']}"
focus_agent = ""

new_tab = "{k['tab_new']}"
rename_tab = "{k['tab_rename']}"
previous_tab = "{k['tab_previous']}"
next_tab = "{k['tab_next']}"
switch_tab = "{digits}"
switch_workspace = ""
close_tab = ""
rename_pane = "{k['pane_rename']}"
edit_scrollback = ""

focus_pane_left = "{k['pane_left']}"
focus_pane_down = ""
focus_pane_up = ""
focus_pane_right = "{k['pane_right']}"
cycle_pane_next = ""
cycle_pane_previous = ""
last_pane = ""
split_vertical = "{k['pane_split']}"
split_horizontal = ""
close_pane = ""
zoom = "{k['pane_zoom']}"
resize_mode = ""
toggle_sidebar = "{k['sidebar_toggle']}"

[[keys.command]]
key = "{k['workspace_new']}"
type = "shell"
command = '"$HERDR_BIN_PATH" workspace create --cwd "$HOME" --focus'
description = "new workspace in $HOME (tabs and panes follow the focused pane)"

[[keys.command]]
key = "{k['theme_toggle']}"
type = "shell"
command = '''
out=$({target.theme_cycle_command} 2>&1) || "$HERDR_BIN_PATH" notification show "테마 전환 실패" --body "$(printf '%s\\n' "$out" | tail -n 1)" --sound none
'''
description = "cycle global terminal theme ({' / '.join(target.theme_names)})"

[[keys.command]]
key = "{k['scroll_bottom_or_copy_exit']}"
type = "shell"
command = '''
pane_id=${{HERDR_ACTIVE_PANE_ID:-}}
test -n "$pane_id" || exit 0
process_info=$("$HERDR_BIN_PATH" pane process-info --pane "$pane_id") || exit 0
shell_pid=$(printf '%s\n' "$process_info" | jq -r '.result.process_info.shell_pid // empty') || exit 0
test -n "$shell_pid" || exit 0
pane_tty=$(ps -o tty= -p "$shell_pid" | tr -d ' ') || exit 0
test -n "$pane_tty" || exit 0
set -- $(stty size < "/dev/$pane_tty") || exit 0
rows=$1
cols=$2
case $rows in ''|*[!0-9]*) exit 0;; esac
case $cols in ''|*[!0-9]*) exit 0;; esac
printf '%s\n' '{{"type":"terminal.input","text":""}}' '{{"type":"terminal.release"}}' | "$HERDR_BIN_PATH" terminal session control "$pane_id" --cols "$cols" --rows "$rows" >/dev/null 2>&1
'''
description = "jump focused pane scrollback to bottom"

[[keys.command]]
key = "cmd+v"
type = "shell"
command = 'test -n "$HERDR_ACTIVE_PANE_ID" && "$HERDR_BIN_PATH" agent send-keys "$HERDR_ACTIVE_PANE_ID" ctrl+v'
description = "paste a clipboard image into the focused agent"

[[keys.command]]
key = "cmd+ㅍ"
type = "shell"
command = 'test -n "$HERDR_ACTIVE_PANE_ID" && "$HERDR_BIN_PATH" agent send-keys "$HERDR_ACTIVE_PANE_ID" ctrl+v'
description = "paste a clipboard image into the focused agent (Korean 2-set)"

[[keys.command]]
key = "ctrl+ㅍ"
type = "shell"
command = 'test -n "$HERDR_ACTIVE_PANE_ID" && "$HERDR_BIN_PATH" pane send-keys "$HERDR_ACTIVE_PANE_ID" ctrl+v'
description = "send physical Ctrl+V while Korean 2-set is active"

[[keys.command]]
key = "ctrl+ㅛ"
type = "shell"
command = 'test -n "$HERDR_ACTIVE_PANE_ID" && "$HERDR_BIN_PATH" pane send-keys "$HERDR_ACTIVE_PANE_ID" ctrl+y'
description = "send physical Ctrl+Y while Korean 2-set is active"

[[keys.command]]
key = "{k['pane_resize_left']}"
type = "shell"
command = '"$HERDR_BIN_PATH" pane resize --pane "$HERDR_ACTIVE_PANE_ID" --direction left --amount 0.1'
description = "resize pane left (Hyper+H)"

[[keys.command]]
key = "{k['pane_resize_down']}"
type = "shell"
command = '"$HERDR_BIN_PATH" pane resize --pane "$HERDR_ACTIVE_PANE_ID" --direction down --amount 0.1'
description = "resize pane down (Hyper+J)"

[[keys.command]]
key = "{k['pane_resize_up']}"
type = "shell"
command = '"$HERDR_BIN_PATH" pane resize --pane "$HERDR_ACTIVE_PANE_ID" --direction up --amount 0.1'
description = "resize pane up (Hyper+K)"

[[keys.command]]
key = "{k['pane_resize_right']}"
type = "shell"
command = '"$HERDR_BIN_PATH" pane resize --pane "$HERDR_ACTIVE_PANE_ID" --direction right --amount 0.1'
description = "resize pane right (Hyper+L)"

[[keys.command]]
key = "{k['yazi']}"
type = "pane"
command = "exec yazi"
description = "open yazi (Hyper+Tab)"

[[keys.command]]
key = "{k['pane_break_right']}"
type = "shell"
command = '{target.move_pane_command} --pane "$HERDR_ACTIVE_PANE_ID"'
description = "move selected vertical-pair pane right and equalize (Hyper+B)"

[[keys.command]]
key = "{k['pane_equalize']}"
type = "plugin_action"
command = "om.pane-equalize.equalize"
description = "equalize current tab pane areas (Hyper+Space)"

# Herdr asks before closing a workspace or its last tab, never a single pane or
# tab; these go through dotfiles/herdr/plugins/confirm-close instead.
[[keys.command]]
key = "{k['tab_close']}"
type = "plugin_action"
command = "confirm-close.confirm-close-tab"
description = "close tab after y/Enter confirmation"

[[keys.command]]
key = "{k['pane_close']}"
type = "plugin_action"
command = "confirm-close.confirm-close-pane"
description = "close pane after y/Enter confirmation"

[[keys.command]]
key = "{k['pane_close_alias']}"
type = "plugin_action"
command = "confirm-close.confirm-close-pane"
description = "close pane after y/Enter confirmation"
{HERDR_END}
"""


def caps_manipulator() -> dict[str, Any]:
    return {
        "from": {
            "key_code": "caps_lock",
            "modifiers": {"optional": ["any"]},
        },
        "to": [
            {
                "key_code": "left_command",
                "modifiers": ["left_control", "left_option"],
            }
        ],
        "type": "basic",
    }


def hyper_rule() -> dict[str, Any]:
    return {"description": HYPER_RULE, "manipulators": [caps_manipulator()]}


KIT_RULE_PREFIX = "terminal-setting: "
HYPER_SOURCES = {"caps_lock": "Caps Lock (한/A)", "right_option": "Right Option"}


def kit_hyper_rule(source: str = "caps_lock", alone: str | None = None) -> dict[str, Any]:
    """The kit's Hyper rule. `alone` is the key sent when the Hyper key is
    pressed and released by itself (F18, bound to macOS "select next input
    source", keeps 한/A switching Korean/English); None makes it Hyper only."""
    if source not in HYPER_SOURCES:
        raise ContractError(f"unknown Hyper key {source!r}; use one of {sorted(HYPER_SOURCES)}")
    manipulator = caps_manipulator()
    manipulator["from"]["key_code"] = source
    label = f"{KIT_RULE_PREFIX}{HYPER_SOURCES[source]} -> Hyper (Ctrl+Option+Command)"
    if alone is not None:
        manipulator["to_if_alone"] = [{"key_code": alone}]
        label += f"; alone -> {alone.upper()}"
    manipulators = [manipulator]
    if source == "caps_lock":
        # Shift+한/A keeps Caps Lock (capitals) once 한/A itself is Hyper.
        manipulators.insert(0, {
            "from": {"key_code": "caps_lock", "modifiers": {"mandatory": ["shift"]}},
            "to": [{"key_code": "caps_lock"}],
            "type": "basic",
        })
        label += "; Shift -> Caps Lock"
    return {"description": label, "manipulators": manipulators}


# User key overrides (terminal-setting-kit `settings.toml` [keys]). A chord is written the way
# Herdr writes it, with "hyper+" accepted for "ctrl+alt+cmd+".
_KEY_NAMES = {
    **{c: (f"key_{c}", ord(c)) for c in "abcdefghijklmnopqrstuvwxyz"},
    **{d: (f"digit_{d}", ord(d)) for d in "0123456789"},
    "=": ("equal", 61),
    "minus": ("minus", 45),
    "[": ("bracket_left", 91),
    "]": ("bracket_right", 93),
    "quote": ("quote", 39),
    "semicolon": ("semicolon", 59),
    "period": ("period", 46),
    "comma": ("comma", 44),
    "space": ("space", 32),
    "tab": ("tab", 9),
    "enter": ("enter", 13),
}
_ARROWS = {"left": "D", "right": "C", "up": "A", "down": "B"}
_KEY_ALIASES = {"-": "minus", "'": "quote", ";": "semicolon", ".": "period", ",": "comma", "equal": "="}
_MODIFIERS = (
    (("ctrl+alt+cmd+", "ctrl+option+command+", "hyper+"), "hyper", "ctrl+alt+cmd+", "ctrl+alt+super+", 15),
    (("cmd+", "command+"), "command", "cmd+", "super+", 9),
)
# macOS and Ghostty own these Command chords (copy, paste, quit, close, ...);
# Cmd+V also carries Herdr's image paste.
RESERVED_CHORDS = {f"cmd+{key}" for key in ("a", "c", "f", "h", "m", "n", "q", "t", "v", "w", "x", "z", "comma", "enter")}
FIXED_ACTIONS = {f"tab_{n}" for n in range(1, 10)}


def parse_chord(chord: str) -> dict[str, Any]:
    text = chord.strip().lower().replace(" ", "")
    for prefixes, input_class, herdr_prefix, ghostty_prefix, modifier in _MODIFIERS:
        prefix = next((p for p in prefixes if text.startswith(p)), None)
        if prefix is not None:
            break
    else:
        raise ContractError(f"{chord!r}: 키는 hyper+… 또는 cmd+… 로 씁니다 (예: hyper+t)")
    key = _KEY_ALIASES.get(text[len(prefix):], text[len(prefix):])
    if key in _ARROWS:
        trigger, csi = f"arrow_{key}", f"1;{modifier}:1{_ARROWS[key]}"
    elif key in _KEY_NAMES:
        trigger, code = _KEY_NAMES[key]
        csi = f"{code};{modifier}:1u"
    else:
        names = ", ".join([*_KEY_NAMES, *_ARROWS])
        raise ContractError(f"{chord!r}: 쓸 수 있는 키가 아닙니다. 쓸 수 있는 키: {names}")
    herdr_key = herdr_prefix + key
    if herdr_key in RESERVED_CHORDS:
        raise ContractError(f"{chord!r}: macOS·Ghostty가 쓰는 키라 바꿀 수 없습니다")
    return {
        "input_class": input_class,
        "ghostty_triggers": [ghostty_prefix + trigger],
        "csi": csi,
        "herdr_key": herdr_key,
    }


def apply_overrides(contract: dict[str, Any], overrides: dict[str, str]) -> dict[str, Any]:
    """Return the contract with the user's chords; "" turns an action off."""
    known = {item["id"] for item in contract["keys"]}
    for action, chord in overrides.items():
        if action not in known:
            raise ContractError(f"{action!r}: 없는 동작입니다. `terminal-setting keys`로 동작 이름을 봅니다")
        if action in FIXED_ACTIONS:
            raise ContractError(f"{action}: 탭 번호 키(Cmd+1~9)는 바꿀 수 없습니다")
        if not isinstance(chord, str):
            raise ContractError(f"{action}: 키는 따옴표 안에 씁니다 (예: \"hyper+t\", 끄려면 \"\")")
    keys = []
    for item in contract["keys"]:
        chord = overrides.get(item["id"])
        if chord is None:
            keys.append(item)
        elif chord.strip():
            keys.append({"id": item["id"], **parse_chord(chord)})
    owners: dict[str, str] = {}
    for item in keys:
        other = owners.setdefault(item["herdr_key"], item["id"])
        if other != item["id"]:
            raise ContractError(f"{item['herdr_key']}: {other}와 {item['id']}가 같은 키입니다")
    validate_keys(keys)
    return {**contract, "keys": keys}


def drop_disabled(herdr_block: str) -> str:
    """Remove what a turned-off action leaves empty in a rendered Herdr block."""
    body, end = herdr_block.rsplit(HERDR_END, 1)
    parts = body.split("\n\n")
    parts = [part for part in parts if not part.lstrip("\n").startswith('[[keys.command]]\nkey = ""')]
    text = "\n\n".join(parts)
    text = re.sub(r'\[("[^"]*"), ""\]', r"\1", text)
    text = re.sub(r'\["", ("[^"]*")\]', r"\1", text)
    if not text.endswith("\n"):
        text += "\n"
    return text + HERDR_END + end

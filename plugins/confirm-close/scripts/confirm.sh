#!/bin/sh
# Real pane with a TTY. Asks y/n once; "y" closes the target pane, then
# exits (dismissing the popup).
set -u

herdr="${HERDR_BIN_PATH:-herdr}"
target="${HERDR_TARGET_PANE_ID:-${HERDR_PANE_ID:-}}"
proc="${HERDR_TARGET_PROCESS:-}"

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# shellcheck disable=SC1091
. "$script_dir/lib.sh"

render_prompt "$herdr" pane "$target" "$proc"

# Single keypress, no echo; restore the terminal on any exit path.
saved=''
if saved=$(stty -g 2>/dev/null); then
  trap 'stty "$saved" 2>/dev/null || true' EXIT INT TERM
  stty -echo -icanon min 1 time 0 2>/dev/null || true
  key=$(dd bs=1 count=1 2>/dev/null)
  # Korean 2-set y arrives as UTF-8 ㅛ (3 bytes); read the rest of it.
  case "$key" in "$(printf '\343')") key="$key$(dd bs=1 count=2 2>/dev/null)" ;; esac
else
  key=$(read line && printf '%s' "$line") # no TTY: fall back to a line read
fi

# Enter reads as "" (command substitution strips the newline); ㅛ is y
# under the Korean IME, which the user types in most of the time.
case "$key" in
  y|Y|ㅛ|'')
    if [ -n "$target" ]; then
      "$herdr" pane close "$target" >/dev/null 2>&1 || true
    fi
    ;;
  *)
    :
    ;;
esac

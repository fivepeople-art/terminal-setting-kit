# Shared by open.sh / open-tab.sh / confirm.sh / confirm-tab.sh. Not meant
# to be executed directly.
#
# Config: plain KEY=VALUE .env at $HERDR_PLUGIN_CONFIG_DIR/.env (same
# convention as herdr-focus-notify/tab-smart-rename), hand-parsed below
# instead of sourced so a value can never run as shell code. Real env vars
# still win over the file.
#
# HERDR_CONFIRM_CLOSE_PLACEMENT        popup (default) or overlay
# HERDR_CONFIRM_CLOSE_POPUP_WIDTH      default 40
# HERDR_CONFIRM_CLOSE_POPUP_HEIGHT     default 5
# HERDR_CONFIRM_CLOSE_REQUIRE_PROCESS  true/false, default false
# HERDR_CONFIRM_CLOSE_WATCH_PROCESSES  space-separated, default unset
# HERDR_CONFIRM_CLOSE_IGNORE_PROCESSES space-separated, default unset

# _load_env_file <path>: sets each KEY=VALUE line as a var, skipping ones
# already set in the real environment. RHS is assigned via `eval "$k=\$v"`
# (blocks re-expansion), so a stray $(...) in a value stays literal text.
_load_env_file() {
  _lef_file="$1"
  [ -f "$_lef_file" ] || return 0
  while IFS= read -r _lef_line || [ -n "$_lef_line" ]; do
    _lef_line=$(printf '%s' "$_lef_line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    case "$_lef_line" in
      '' | '#'*) continue ;;
      export\ *) _lef_line=${_lef_line#export } ;;
    esac
    case "$_lef_line" in
      *=*) ;;
      *) continue ;;
    esac
    _lef_key=${_lef_line%%=*}
    _lef_value=${_lef_line#*=}
    case "$_lef_key" in
      [A-Za-z_]*)
        case "$_lef_key" in
          *[!A-Za-z0-9_]*) continue ;;
        esac
        ;;
      *) continue ;;
    esac
    case "$_lef_value" in
      # Quoted: keep everything up to the first matching closing quote,
      # discarding anything after it (e.g. a trailing comment). No escape
      # support -- one layer of quotes only, same as before.
      \"*) _lef_value=${_lef_value#\"} ; _lef_value=${_lef_value%%\"*} ;;
      \'*) _lef_value=${_lef_value#\'} ; _lef_value=${_lef_value%%\'*} ;;
      # Unquoted: strip a trailing " #comment" (only when '#' is preceded
      # by whitespace, so e.g. "abc#123" stays literal), then trim.
      *) _lef_value=$(printf '%s' "$_lef_value" | sed -e 's/[[:space:]]#.*$//' -e 's/[[:space:]]*$//') ;;
    esac
    if eval "[ -z \"\${$_lef_key+x}\" ]"; then
      eval "$_lef_key=\$_lef_value"
    fi
  done < "$_lef_file"
}

if [ -n "${HERDR_PLUGIN_CONFIG_DIR:-}" ]; then
  _load_env_file "$HERDR_PLUGIN_CONFIG_DIR/.env" 2>/dev/null || true
fi

PLACEMENT="${HERDR_CONFIRM_CLOSE_PLACEMENT:-popup}"
POPUP_WIDTH="${HERDR_CONFIRM_CLOSE_POPUP_WIDTH:-64}"
POPUP_HEIGHT="${HERDR_CONFIRM_CLOSE_POPUP_HEIGHT:-6}"
REQUIRE_PROCESS="${HERDR_CONFIRM_CLOSE_REQUIRE_PROCESS:-false}"
# Empty = no allowlist, anything non-shell counts (see pane_active_process).
WATCH_PROCESSES="${HERDR_CONFIRM_CLOSE_WATCH_PROCESSES:-}"
# Empty = no denylist, nothing is excluded (see pane_active_process).
IGNORE_PROCESSES="${HERDR_CONFIRM_CLOSE_IGNORE_PROCESSES:-}"

# pane_active_process <herdr_bin> <pane_id>: true if something other than
# the pane's own shell is in the foreground (WezTerm's close-confirmation
# heuristic -- shell_pid vs foreground_process_group_id from `herdr pane
# process-info`, equal only when idle). WATCH_PROCESSES, if set, narrows
# this to specific argv0 names. IGNORE_PROCESSES, if set, is checked first
# and excludes specific argv0 names from ever blocking the close, even if
# WATCH_PROCESSES would otherwise match them.
#
# Three-way result, since "should we skip the prompt?" and "did detection
# actually work?" are different questions -- a lookup failure must not be
# treated the same as a confirmed-idle pane, or callers would silently
# close panes they couldn't inspect:
#   0  active and (if WATCH_PROCESSES is set) matched -- prints the name.
#   1  confirmed idle, or a known process excluded by WATCH_PROCESSES or
#      IGNORE_PROCESSES -- safe for the caller to close without prompting.
#   2  unknown (lookup/parse failed, or active but unidentifiable) --
#      caller should prompt rather than guess.
pane_active_process() {
  _pap_herdr="$1"
  _pap_pane_id="$2"
  [ -n "$_pap_pane_id" ] || return 2
  _pap_info=$("$_pap_herdr" pane process-info --pane "$_pap_pane_id" 2>/dev/null) || return 2

  _pap_shell_pid=$(printf '%s' "$_pap_info" | sed -n 's/.*"shell_pid":\([0-9]*\).*/\1/p')
  _pap_fg_pgid=$(printf '%s' "$_pap_info" | sed -n 's/.*"foreground_process_group_id":\([0-9]*\).*/\1/p')
  [ -n "$_pap_shell_pid" ] && [ -n "$_pap_fg_pgid" ] || return 2
  [ "$_pap_shell_pid" != "$_pap_fg_pgid" ] || return 1

  # argv0 of the group leader; more reliable than `name` (seen filled with
  # a bare version string for a claude pane). herdr always emits "pid" as
  # the last field in a process object, right before its closing '}' --
  # no need to also match end-of-line.
  _pap_line=$(printf '%s' "$_pap_info" | tr '{' '\n' | grep "\"pid\":$_pap_fg_pgid[,}]")
  _pap_name=$(printf '%s' "$_pap_line" | sed -n 's/.*"argv0":"\([^"]*\)".*/\1/p')
  [ -n "$_pap_name" ] || return 2 # active but couldn't identify it

  if [ -n "$IGNORE_PROCESSES" ]; then
    for _pap_skip in $IGNORE_PROCESSES; do
      [ "$_pap_name" = "$_pap_skip" ] && return 1 # explicitly excluded
    done
  fi

  if [ -n "$WATCH_PROCESSES" ]; then
    _pap_matched=0
    for _pap_want in $WATCH_PROCESSES; do
      if [ "$_pap_name" = "$_pap_want" ]; then
        _pap_matched=1
        break
      fi
    done
    [ "$_pap_matched" = 1 ] || return 1 # identified, just not watched
  fi

  printf '%s' "$_pap_name"
  return 0
}

# capitalize <string>: uppercase the first character, e.g. claude -> Claude.
capitalize() {
  _cap_first=$(printf '%s' "$1" | cut -c1 | tr '[:lower:]' '[:upper:]')
  _cap_rest=$(printf '%s' "$1" | cut -c2-)
  printf '%s%s' "$_cap_first" "$_cap_rest"
}

# set_placement_args: POSIX sh has no arrays and a function's `set --` only
# lasts for its own scope, so this sets $PLACEMENT_ARGS as a string instead;
# callers do `set -- $PLACEMENT_ARGS` (deliberately unquoted, safe here).
set_placement_args() {
  PLACEMENT_ARGS="--placement $PLACEMENT"
  if [ "$PLACEMENT" = "popup" ]; then
    PLACEMENT_ARGS="$PLACEMENT_ARGS --width $POPUP_WIDTH --height $POPUP_HEIGHT"
  fi
}

# theme_color <role> <ansi_fallback>: SGR color body for a Herdr palette role
# from [theme.custom] in the live config (the theme cycle rewrites it), e.g.
# "38;2;161;47;47". Prints the ANSI fallback when the role is not there.
theme_color() {
  _tc_hex=$(sed -n '/^\[theme\.custom\]/,/^\[/s/^'"$1"' *= *"#\([0-9a-fA-F]\{6\}\)".*/\1/p' \
    "${HERDR_CONFIG_PATH:-$HOME/.config/herdr/config.toml}" 2>/dev/null | head -n 1)
  if [ -n "$_tc_hex" ]; then
    printf '2;%d;%d;%d' "0x$(printf '%s' "$_tc_hex" | cut -c1-2)" \
      "0x$(printf '%s' "$_tc_hex" | cut -c3-4)" "0x$(printf '%s' "$_tc_hex" | cut -c5-6)"
  else
    printf '%s' "$2"
  fi
}

# render_prompt <herdr_bin> <pane|tab> <target_id> <proc>: the popup body,
# drawn like Herdr's own close-workspace dialog (render_confirm_close_overlay):
# a 64x6 popup, bold red title, "<name> — <detail>", then "↵ confirm" on red
# and "esc cancel" on surface0, 13 and 12 cells wide, 2 apart, centered.
render_prompt() {
  _rp_herdr="$1"; _rp_kind="$2"; _rp_id="$3"; _rp_proc="$4"
  _rp_jq='def cut(n): if length > n then .[0:n-1] + "…" else . end;
    def agents: [.[] | select(.agent) | "\(.agent) \(.agent_status)"] | join(" · ");'
  if [ "$_rp_kind" = tab ]; then
    _rp_title='Close tab?'
    _rp_info=$("$_rp_herdr" tab get "$_rp_id" 2>/dev/null) || _rp_info=''
    _rp_name=$(printf '%s' "$_rp_info" | jq -r "$_rp_jq"'.result.tab.label // "" | cut(24)' 2>/dev/null)
    _rp_ws=$(printf '%s' "$_rp_info" | jq -r '.result.tab.workspace_id // ""' 2>/dev/null)
    _rp_detail=''
    if [ -n "$_rp_ws" ]; then
      _rp_detail=$("$_rp_herdr" pane list --workspace "$_rp_ws" 2>/dev/null | jq -r --arg t "$_rp_id" "$_rp_jq"'
        [.result.panes[] | select(.tab_id == $t)] as $p
        | ($p | length) as $n | ($p | agents) as $a
        | "\($n) pane\(if $n == 1 then "" else "s" end)" + (if $a == "" then "" else " · " + $a end)' 2>/dev/null)
    fi
  else
    _rp_title='Close pane?'
    _rp_info=$("$_rp_herdr" pane get "$_rp_id" 2>/dev/null) || _rp_info=''
    _rp_name=$(printf '%s' "$_rp_info" | jq -r "$_rp_jq"'.result.pane.label // "" | cut(24)' 2>/dev/null)
    _rp_detail=$(printf '%s' "$_rp_info" | jq -r "$_rp_jq"'[.result.pane] | agents' 2>/dev/null)
  fi
  [ -n "$_rp_detail" ] || _rp_detail="$_rp_proc"
  _rp_line=${_rp_name:-$_rp_id}
  [ -z "$_rp_detail" ] || _rp_line="$_rp_line — $_rp_detail"

  _rp_red=$(theme_color red 1)
  _rp_text=$(theme_color text 9)
  _rp_bg=$(theme_color panel_bg 9)
  _rp_surface=$(theme_color surface0 7)
  _rp_fg="3$_rp_text"; _rp_on_red="4$_rp_red;3$_rp_bg"
  case "$_rp_text" in 2\;*) _rp_fg="38;$_rp_text" ;; esac
  case "$_rp_red" in 2\;*) _rp_on_red="48;$_rp_red;38;$_rp_bg" ;; esac
  case "$_rp_bg" in 9) _rp_on_red="4$_rp_red;37" ;; esac
  _rp_redfg="3$_rp_red"; _rp_surfbg="4$_rp_surface"
  case "$_rp_red" in 2\;*) _rp_redfg="38;$_rp_red" ;; esac
  case "$_rp_surface" in 2\;*) _rp_surfbg="48;$_rp_surface" ;; esac

  # Hide the cursor, clip instead of wrapping long names, draw from the top.
  printf '\033[?25l\033[?7l\033[H'
  printf ' \033[1;%sm%s\033[0m\n' "$_rp_redfg" "$_rp_title"
  printf ' \033[%sm%s\033[0m\n' "$_rp_fg" "$_rp_line"
  printf '\n'
  _rp_cols=$(stty size 2>/dev/null | cut -d' ' -f2)
  _rp_pad=$(( (${_rp_cols:-62} - 27) / 2 ))
  [ "$_rp_pad" -ge 0 ] || _rp_pad=0
  printf '%*s\033[1;%sm  ↵ confirm  \033[0m  \033[1;%s;%sm esc cancel \033[0m' \
    "$_rp_pad" '' "$_rp_on_red" "$_rp_fg" "$_rp_surfbg"
}

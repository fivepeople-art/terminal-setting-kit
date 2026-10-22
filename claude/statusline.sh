#!/usr/bin/env bash
# Claude Code status line
# Shows, on two lines:
#   model effort · context left · 5h left + reset · session cost
#   session name · cache TTL left · 7d left + reset · dir:branch (+dirty)
# Inside Herdr it also reports the context-left figure to the agent sidebar.
# Reads the status JSON payload from stdin.

input="$(cat)"

# Colors are ANSI slots, never Hex, so Ghostty's palette stays the only color
# source: this block only decides which slot plays each role. Dim halves
# contrast, so it is used for the generic map's quiet parts only.
RESET=$'\033[0m'

# The toggle helper writes a single "theme = NAME" line into Ghostty's config;
# reading it here is one small-file read per refresh.
ghostty_theme=$(sed -n 's/^[[:space:]]*theme[[:space:]]*=[[:space:]]*//p' \
  "${XDG_CONFIG_HOME:-$HOME/.config}/ghostty/config" 2>/dev/null | tail -n 1)

case "$ghostty_theme" in
  fapibrown)
    # Warm ground #1e1c18. Color means attention: in the normal state the line
    # stays cream and grey, and only running-low (gold, slot 3), nearly
    # exhausted and the dirty marker (bold terracotta, slot 173) take a hue.
    # Terracotta is the one orange, shared with Claude Code's bypass footer
    # (slot 9 #cc734d) right below; four near-oranges (model #fd9f4d, name
    # peach #fecea0, rust #cb4a05, terracotta) read as a mismatch (user). The
    # model takes bold ivory (slot 15), figures and the session name the prose
    # cream through slot 230 (Claude Code dims default-colored text to grey),
    # bars the secondary grey over the slot 8 track. The directory keeps the
    # bundled brown (slot 137; sage and steel blue were rejected). Contrast on
    # #1e1c18 is noted per slot.
    C_SEP=$'\033[90m'      # slot 8  #808067 4.2:1 - separators (decorative)
    C_LABEL=$'\033[37m'    # slot 7  #a19981 6.0:1 - labels, effort, countdown
    C_MODEL=$'\033[1;97m'  # slot 15 #fff8ea 16.7:1 - model
    C_OK=$'\033[38;5;230m' # slot 230 #d3cda6 10.6:1 - plenty left (figure)
    C_FILL_OK=$'\033[37m'  # slot 7  #a19981 6.0:1 - plenty left (bar)
    C_WARN=$'\033[33m'     # slot 3  #fecf75 11.7:1 - running low
    C_CRIT=$'\033[1;38;5;173m' # slot 173 #cc734d 5.0:1 - nearly exhausted
    C_NAME=$'\033[38;5;230m' # slot 230 #d3cda6 10.6:1 - session name
    C_DIR=$'\033[38;5;137m' # slot 137 #9e744d 4.1:1 - directory
    C_GIT=$'\033[37m'      # slot 7  #a19981 6.0:1 - branch
    C_DIRTY=$'\033[38;5;173m' # slot 173 #cc734d 5.0:1 - dirty marker
    C_TRACK=$'\033[90m'    # slot 8  #808067 - empty part of a usage bar
    ;;
  "Eyes Day")
    # Cream ground. Like fapibrown, color means attention: the normal state
    # stays in ink and greys, and only running low (ochre, slot 3), nearly
    # exhausted and the dirty marker (bold rose, slot 9, the same red as
    # Claude Code's bypass footer right below) take a hue. The model takes
    # bold slot 0 ink, figures and the session name the body text through
    # extended slot 230, bars slot 8 over its dimmed track (about 3:1), the
    # directory the deep teal and the branch the secondary grey. Green
    # figures, a teal model, rust directory and plum branch read as too many
    # hues (user standard). Contrast on #fdf6e3 is noted per slot.
    C_SEP=$'\033[2;90m'    # slot 8  #787063 dimmed ~3:1 - separators
    C_LABEL=$'\033[90m'    # slot 8  #787063 4.5:1 - labels, effort, countdown
    C_MODEL=$'\033[1;30m'  # slot 0  #24211b 14.9:1 - model
    C_OK=$'\033[38;5;230m' # slot 230 #353129 12.0:1 - plenty left (figure)
    C_FILL_OK=$'\033[90m'  # slot 8  #787063 4.5:1 - plenty left (bar)
    C_WARN=$'\033[33m'     # slot 3  #805900 5.8:1 - running low
    C_CRIT=$'\033[1;91m'   # slot 9  #aa3f46 5.5:1 - nearly exhausted
    C_NAME=$'\033[38;5;230m' # slot 230 #353129 12.0:1 - session name
    C_DIR=$'\033[36m'      # slot 6  #00635b 6.6:1 - directory
    C_GIT=$'\033[90m'      # slot 8  #787063 4.5:1 - branch
    C_DIRTY=$'\033[1;91m'  # slot 9  #aa3f46 5.5:1 - dirty marker
    C_TRACK=$'\033[2;90m'  # slot 8  #787063 dimmed ~3:1 - empty part of a usage bar
    ;;
  "Eyes Night")
    # Moss-ink ground #131f18. Like fapibrown, color means attention: the line
    # stays in the theme's sage greens and greys, and only running low (wheat,
    # slot 3), nearly exhausted and the dirty marker (bold terracotta, slot 1)
    # take another hue. The teal model, sky-blue directory and mauve branch
    # read as four unrelated hues on the green ground (user). The model takes
    # bold slot 15, the session name the body text through extended slot 230
    # (Claude Code dims default-colored text to grey), the directory the
    # theme's sage teal and the branch the secondary grey. Contrast on #131f18
    # is noted per slot.
    C_SEP=$'\033[90m'      # slot 8  #7a8980 4.6:1 - separators (decorative)
    C_LABEL=$'\033[37m'    # slot 7  #9ca79a 6.8:1 - labels, effort, countdown
    C_MODEL=$'\033[1;97m'  # slot 15 #e9ede2 14.3:1 - model
    C_OK=$'\033[92m'       # slot 10 #b9cea1 10.0:1 - plenty left (figure)
    C_FILL_OK=$'\033[32m'  # slot 2  #9cb57e 7.5:1 - plenty left (bar)
    C_WARN=$'\033[33m'     # slot 3  #ceac6d 7.9:1 - running low
    C_CRIT=$'\033[1;31m'   # slot 1  #d99685 7.0:1 - nearly exhausted
    C_NAME=$'\033[38;5;230m' # slot 230 #d1d9cb 11.7:1 - session name
    C_DIR=$'\033[36m'      # slot 6  #7fb8b0 7.6:1 - directory
    C_GIT=$'\033[37m'      # slot 7  #9ca79a 6.8:1 - branch
    C_DIRTY=$'\033[1;31m'  # slot 1  #d99685 7.0:1 - dirty marker
    C_TRACK=$'\033[90m'    # slot 8  #7a8980 4.6:1 - empty part of a usage bar
    ;;
  *)
    # Generic map for any other theme.
    C_SEP=$'\033[2;39m'    # dim default foreground
    C_LABEL=$'\033[2;39m'  # dim default foreground
    C_MODEL=$'\033[36m'    # cyan
    C_OK=$'\033[2;39m'     # dim default foreground (figure)
    C_FILL_OK=$'\033[32m'  # green (bar)
    C_WARN=$'\033[33m'     # yellow
    C_CRIT=$'\033[1;31m'   # bold red
    C_NAME=$'\033[33m'     # yellow
    C_DIR=$'\033[95m'      # bright magenta
    C_GIT=$'\033[92m'      # bright green
    C_DIRTY=$'\033[31m'    # red
    # Slot 7, not 8: OM Solarized Light's slot 8 is near-black and would read
    # as a filled bar, while its slot 7 (#bbb5a2) is a faint track on cream.
    C_TRACK=$'\033[37m'    # white - empty part of a usage bar
    ;;
esac

# One jq call fills every field. Keeping it to a single process matters because
# the status line re-runs on every session event, not just the refresh interval.
if command -v jq >/dev/null 2>&1; then
  # One field per line, not @tsv: bash treats TAB as IFS whitespace, so a run of
  # empty fields would collapse and shift every value after it into the wrong
  # variable. Line-separated fields keep empty values in place.
  {
    IFS= read -r model
    IFS= read -r effort
    IFS= read -r cwd
    IFS= read -r project_dir
    IFS= read -r ctx_left
    IFS= read -r five_used
    IFS= read -r five_reset
    IFS= read -r seven_used
    IFS= read -r seven_reset
    IFS= read -r session_name
    IFS= read -r cache_warm
    IFS= read -r cache_ttl
    IFS= read -r cache_exp
    IFS= read -r cost_usd
  } <<EOF
$(printf '%s' "$input" | jq -r '
  # East Asian glyphs occupy two terminal columns, so the session name is
  # trimmed by display width rather than character count. jq does the trimming
  # because bash 3.2 cannot slice multi-byte strings on character boundaries.
  # Decimal because jq has no hex literals; these are the wcwidth
  # wide/fullwidth ranges (U+1100-115F, CJK, Hangul, fullwidth forms).
  def cw:
    if . == 9001 or . == 9002
       or (. >= 4352 and . <= 4447)
       or (. >= 11904 and . <= 42191 and . != 12351)
       or (. >= 44032 and . <= 55203)
       or (. >= 63744 and . <= 64255)
       or (. >= 65072 and . <= 65135)
       or (. >= 65280 and . <= 65376)
       or (. >= 65504 and . <= 65510)
    then 2 else 1 end;
  def dwidth: explode | map(cw) | add // 0;
  def trunc($max):
    if dwidth <= $max then .
    else ( reduce (explode[]) as $c ({a: [], w: 0, done: false};
             if .done then .
             elif (.w + ($c | cw)) <= ($max - 1)
             then {a: (.a + [$c]), w: (.w + ($c | cw)), done: false}
             else {a: .a, w: .w, done: true} end)
           | .a | implode ) + "…"
    end;
  # "Opus 5 (1M context)" -> "Opus 5 1M": the size already reads as a context
  # window, so the word and the parentheses are redundant in a line this tight.
  [ ((.model.display_name // "") | gsub(" \\((?<c>[^)]*) context\\)"; " \(.c)"))
  , (.effort.level // "")
  , (.workspace.current_dir // .cwd // "")
  , (.workspace.project_dir // "")
  , (.context_window.remaining_percentage // "" | tostring)
  , (.rate_limits.five_hour.used_percentage // "" | tostring)
  , (.rate_limits.five_hour.resets_at // "" | tostring)
  , (.rate_limits.seven_day.used_percentage // "" | tostring)
  , (.rate_limits.seven_day.resets_at // "" | tostring)
  , ((.session_name // "") | gsub("[\\n\\r\\t]"; " ") | trunc(30))
  # Not `// ""`: jq treats false as missing there, which would hide "cold".
  , (if .prompt_cache.warm == null then "" else (.prompt_cache.warm | tostring) end)
  , (.prompt_cache.ttl // "")
  , (.prompt_cache.expires_at // "" | tostring)
  , (.cost.total_cost_usd // "" | tostring)
  ] | .[]')
EOF
else
  # jq missing: fall back to sane defaults so the status line still renders.
  model=""; effort=""; cwd=""; project_dir=""; ctx_left=""; five_used=""
  five_reset=""; seven_used=""; seven_reset=""; session_name=""; cache_warm=""
  cache_ttl=""; cache_exp=""; cost_usd=""
fi

[ -n "$model" ] || model="Claude"
[ -n "$cwd" ] || cwd="$PWD"

# Name the location after the project root: the root's own name, plus the path
# below it when Claude has moved into a subdirectory. Outside the project, fall
# back to the ~-abbreviated path. Deep paths are shortened so they never crowd
# out the segments that change.
if [ -n "$project_dir" ] && [ "$project_dir" != "$HOME" ] && [ "$project_dir" != "/" ] &&
   { [ "$cwd" = "$project_dir" ] || [ "${cwd#"$project_dir"/}" != "$cwd" ]; }; then
  project_name="${project_dir##*/}"
  dir="${project_name}${cwd#"$project_dir"}"
else
  case "$cwd" in
    "$HOME") dir="~" ;;
    "$HOME"/*) dir="~${cwd#"$HOME"}" ;;
    *) dir="$cwd" ;;
  esac
fi
if [ "${#dir}" -gt 24 ] && [ -n "$project_name" ] && [ "$cwd" != "$project_dir" ]; then
  # Inside the project, keep its name and the leaf rather than the middle.
  dir="${project_name}/…/${dir##*/}"
elif [ "${#dir}" -gt 24 ]; then
  leaf="${dir##*/}"
  parent="${dir%/*}"
  parent="${parent##*/}"
  if [ -n "$parent" ]; then
    dir="…/${parent}/${leaf}"
  else
    dir="…/${leaf}"
  fi
  [ "${#dir}" -gt 24 ] && dir="…/${leaf}"
fi

# Three bands of the share left: calm above 50%, yellow from 50% down, red at
# 20% and below. Context uses 70%/40% instead (passed as the 2nd/3rd argument):
# cost climbs long before the window fills, from about 300k tokens used.
# The figure and the bar share the warning colors but not the calm one, so a
# calm bar keeps its own fill.
# Herdr's agent sidebar shows the same context-left figure next to the agent
# name. One token per color level (ctx_ok, ctx_warn, ctx_crit, styled in
# Herdr's config.toml) because Herdr's rules can't compare "34%" as a number.
# Reports only inside a Herdr pane, in the background so the status line never
# waits, and only when the figure changed or a minute passed; the TTL clears
# the token once Claude stops refreshing (pane back to a shell).
report_ctx_to_herdr() {
  [ -n "$HERDR_PANE_ID" ] && [ -z "$STATUSLINE_NO_HERDR" ] || return 0
  command -v herdr >/dev/null 2>&1 || return 0
  local level=ok
  if [ "$1" -le 40 ]; then level=crit; elif [ "$1" -le 70 ]; then level=warn; fi
  local stamp="${TMPDIR:-/tmp}/herdr-ctx-${HERDR_PANE_ID//[^A-Za-z0-9]/_}"
  local now last_val="" last_at=0
  now=$(date +%s)
  [ -r "$stamp" ] && read -r last_val last_at < "$stamp"
  [ "$last_val" = "$1" ] && [ $((now - last_at)) -lt 60 ] && return 0
  printf '%s %s\n' "$1" "$now" > "$stamp"
  local args=() l
  for l in ok warn crit; do
    if [ "$l" = "$level" ]; then
      args+=(--token "ctx_$l=$1%")
    else
      args+=(--clear-token "ctx_$l")
    fi
  done
  (herdr pane report-metadata "$HERDR_PANE_ID" --source statusline.ctx \
    --ttl-ms 180000 "${args[@]}" >/dev/null 2>&1 &)
}

color_for_left() {
  if [ "$1" -le "${3:-20}" ]; then
    printf '%s' "$C_CRIT"
  elif [ "$1" -le "${2:-50}" ]; then
    printf '%s' "$C_WARN"
  else
    printf '%s' "$C_OK"
  fi
}

fill_for_left() {
  if [ "$1" -gt "${2:-50}" ]; then
    printf '%s' "$C_FILL_OK"
  else
    color_for_left "$@"
  fi
}

# Draw a 10-cell gauge for a 0-100 share left in 5% steps: heavy line for what
# is left, light line for what is spent, and a heavy-to-light cell for an odd
# half. Weight carries the reading even without color, and Ghostty draws box
# drawing edge to edge, so the cells join into one slim line.
left_bar() {
  local halves=$(( ($1 + 2) / 5 )) i fill="" track=""
  [ "$halves" -gt 20 ] && halves=20
  for (( i = 0; i < halves / 2; i++ )); do fill="${fill}━"; done
  [ $(( halves % 2 )) -eq 1 ] && fill="${fill}╾"
  for (( i = (halves + 1) / 2; i < 10; i++ )); do track="${track}─"; done
  printf '%s' "${2}${fill}${RESET}${C_TRACK}${track}${RESET}"
}

# Turn a used percentage into the whole share left, clamped to 0-100. The
# payload value may be fractional, so the arithmetic goes to awk; anything
# unparseable prints nothing and the caller drops its segment.
pct_left() {
  local r
  r=$(awk -v u="$1" \
    'BEGIN { r = 100 - u; if (r < 0) r = 0; if (r > 100) r = 100; printf "%d", r + 0.5 }' 2>/dev/null)
  case "$r" in
    ''|*[!0-9]*) ;;
    *) printf '%s' "$r" ;;
  esac
}

# Countdown to a resets_at epoch: "2d05h" beyond a day, "4h08m" within one,
# "28m" in the last hour. Prints nothing once the reset has passed or when the
# value is unparseable, so the caller simply omits it.
countdown() {
  local left_s d h m
  left_s=$(awk -v t="$1" -v n="$(date +%s)" \
    'BEGIN { d = int(t - n); if (d < 0) d = 0; print d }' 2>/dev/null)
  case "$left_s" in
    ''|*[!0-9]*) return ;;
  esac
  [ "$left_s" -gt 0 ] || return
  d=$(( left_s / 86400 ))
  h=$(( (left_s % 86400) / 3600 ))
  m=$(( (left_s % 3600) / 60 ))
  if [ "$d" -gt 0 ]; then
    printf '%dd%02dh' "$d" "$h"
  elif [ "$h" -gt 0 ]; then
    printf '%dh%02dm' "$h" "$m"
  else
    printf '%dm' "$m"
  fi
}

# Every figure and gauge shows what is left, like a fuel gauge: a bar drains
# toward trouble and matches the countdowns beside it, and the colors follow
# the same share, so the line carries no "used"/"left" words.
segments=()

# Effort is absent for models without an effort setting.
model_txt="${C_MODEL}${model}${RESET}"
[ -n "$effort" ] && model_txt="${model_txt} ${C_LABEL}${effort}${RESET}"
segments+=("$model_txt")

# Context window left. The payload pre-calculates the remaining share, so the
# figure, the bar and the color all come from one rounded value.
if [ -n "$ctx_left" ]; then
  ctx_fmt=$(printf '%.0f' "$ctx_left" 2>/dev/null)
  case "$ctx_fmt" in
    ''|*[!0-9]*) ctx_fmt="" ;;
  esac
  if [ -n "$ctx_fmt" ]; then
    c_ctx=$(color_for_left "$ctx_fmt" 70 40)
    segments+=("${C_LABEL}ctx${RESET} $(left_bar "$ctx_fmt" "$(fill_for_left "$ctx_fmt" 70 40)") ${c_ctx}${ctx_fmt}%${RESET}")
    report_ctx_to_herdr "$ctx_fmt"
  fi
fi

# Rolling 5-hour and weekly rate limit windows. rate_limits is present only for
# claude.ai Pro/Max subscriptions, and only after the first API response, so
# these segments stay absent otherwise.
[ -n "$five_used" ] && five_left=$(pct_left "$five_used")
if [ -n "$five_left" ]; then
  c_five=$(color_for_left "$five_left")
  five_txt="${C_LABEL}5h${RESET} $(left_bar "$five_left" "$(fill_for_left "$five_left")") ${c_five}${five_left}%${RESET}"
  # Countdown to the reset, from the resets_at epoch seconds.
  five_cd=$(countdown "$five_reset")
  [ -n "$five_cd" ] && five_txt="${five_txt} ${C_LABEL}${five_cd}${RESET}"
  segments+=("$five_txt")
fi

# Session cost: Claude Code's list-price estimate for this session, not the
# bill (a subscription pays nothing extra), reset by /clear. A plain figure
# with no warning color, since no limit hangs on it.
if [ -n "$cost_usd" ]; then
  cost_fmt=$(awk -v c="$cost_usd" 'BEGIN { if (c ~ /^[0-9.]+$/) printf "%.2f", c }' 2>/dev/null)
  [ -n "$cost_fmt" ] && segments+=("${C_OK}\$${cost_fmt}${RESET}")
fi

# Everything from here on goes on the second line: the model and the figures
# that move within minutes stay on the first, where they line up.
line2_start=${#segments[@]}

# Session name: the custom name from --name or /rename, otherwise the generated
# session title. Absent until the session has one, so the segment is optional.
if [ -n "$session_name" ]; then
  segments+=("${C_NAME}${session_name}${RESET}")
fi

# Prompt cache countdown from the payload's prompt_cache block, present after
# the main conversation's first API response. Claude Code re-runs the script
# when expires_at passes, so "cold" appears on time even between refreshes.
# The label names the TTL only when it is the short one (overage drops to 5m).
# It sits right after the session name, the first thing on the second line.
if [ -n "$cache_warm" ]; then
  cache_label="cache"
  cache_len=3600
  if [ "$cache_ttl" = "5m" ]; then
    cache_label="cache(5m)"
    cache_len=300
  fi
  cache_left=0
  case "$cache_exp" in
    ''|*[!0-9]*) ;;
    *) [ "$cache_warm" = "true" ] && cache_left=$(( cache_exp - $(date +%s) )) ;;
  esac
  if [ "$cache_left" -le 0 ]; then
    segments+=("${C_LABEL}${cache_label}${RESET} ${C_CRIT}cold${RESET}")
  else
    # Round up so a fresh response reads "60m", and the last minute "1m".
    cache_min=$(( (cache_left + 59) / 60 ))
    # The figure alone, warning colors taken from the share of the TTL left.
    c_cache=$(color_for_left "$(( cache_left * 100 / cache_len ))")
    segments+=("${C_LABEL}${cache_label}${RESET} ${c_cache}${cache_min}m${RESET}")
  fi
fi

# The weekly window barely moves within a session, so it sits on the second
# line after the session name rather than beside the bars.
[ -n "$seven_used" ] && seven_left=$(pct_left "$seven_used")
if [ -n "$seven_left" ]; then
  c_seven=$(color_for_left "$seven_left")
  seven_txt="${C_LABEL}7d${RESET} ${c_seven}${seven_left}%${RESET}"
  seven_cd=$(countdown "$seven_reset")
  [ -n "$seven_cd" ] && seven_txt="${seven_txt} ${C_LABEL}${seven_cd}${RESET}"
  segments+=("$seven_txt")
fi

# Location comes last as one "dir:branch*" segment. The branch and dirty marker
# are not in the payload, so the script derives them, and skips them entirely
# when cwd is not a git repo.
loc="${C_DIR}${dir}${RESET}"
if git -C "$cwd" --no-optional-locks rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch=$(git -C "$cwd" --no-optional-locks rev-parse --abbrev-ref HEAD 2>/dev/null)
  if [ -n "$branch" ]; then
    dirty=""
    if [ -n "$(git -C "$cwd" --no-optional-locks status --porcelain 2>/dev/null)" ]; then
      dirty="${C_DIRTY}*${RESET}"
    fi
    loc="${loc}${C_SEP}:${RESET}${C_GIT}${branch}${RESET}${dirty}"
  fi
fi
segments+=("$loc")

# Join a range of segments with a dim middle dot.
join_segments() {
  local out="" i
  for (( i = $1; i < $2; i++ )); do
    if [ -z "$out" ]; then
      out="${segments[$i]}"
    else
      out="${out} ${C_SEP}·${RESET} ${segments[$i]}"
    fi
  done
  printf '%s' "$out"
}

# Claude Code renders each output line as its own status line row.
printf '%s\n' "$(join_segments 0 "$line2_start")"
printf '%s\n' "$(join_segments "$line2_start" "${#segments[@]}")"

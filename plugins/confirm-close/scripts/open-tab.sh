#!/bin/sh
# Opens the confirmation popup, or (if REQUIRE_PROCESS is set and nothing's
# active here) closes the tab straight away. Only checks the tab's focused
# pane (HERDR_PANE_ID) -- an unfocused split won't be detected.
set -eu

herdr="${HERDR_BIN_PATH:-herdr}"
target="${HERDR_TAB_ID:-}"
focused_pane="${HERDR_PANE_ID:-}"

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# shellcheck disable=SC1091
. "$script_dir/lib.sh"

proc=""
if [ "$REQUIRE_PROCESS" = "true" ]; then
  if proc=$(pane_active_process "$herdr" "$focused_pane"); then
    : # active match, $proc already set
  else
    _status=$?
    if [ "$_status" = 1 ]; then
      exec "$herdr" tab close "$target" # confirmed idle
    fi
    proc="" # unknown (status 2): prompt rather than guess
  fi
fi

set_placement_args
set -- $PLACEMENT_ARGS # deliberately unquoted, see lib.sh
exec "$herdr" plugin pane open \
  --plugin confirm-close \
  --entrypoint confirm-tab \
  "$@" \
  --focus \
  --env "HERDR_TARGET_TAB_ID=$target" \
  --env "HERDR_TARGET_PROCESS=$proc"

#!/bin/sh
# Opens the confirmation popup, or (if REQUIRE_PROCESS is set and nothing's
# active here) closes the pane straight away.
set -eu

herdr="${HERDR_BIN_PATH:-herdr}"
target="${HERDR_PANE_ID:-}"

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# shellcheck disable=SC1091
. "$script_dir/lib.sh"

proc=""
if [ "$REQUIRE_PROCESS" = "true" ]; then
  if proc=$(pane_active_process "$herdr" "$target"); then
    : # active match, $proc already set
  else
    _status=$?
    if [ "$_status" = 1 ]; then
      exec "$herdr" pane close "$target" # confirmed idle
    fi
    proc="" # unknown (status 2): prompt rather than guess
  fi
fi

set_placement_args
set -- $PLACEMENT_ARGS # deliberately unquoted, see lib.sh
exec "$herdr" plugin pane open \
  --plugin confirm-close \
  --entrypoint confirm \
  "$@" \
  --focus \
  --env "HERDR_TARGET_PANE_ID=$target" \
  --env "HERDR_TARGET_PROCESS=$proc"

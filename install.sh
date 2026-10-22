#!/bin/sh
# terminal-setting-kit installer. Paste into Terminal:
#   curl -fsSL https://raw.githubusercontent.com/fivepeople-art/terminal-setting-kit/main/install.sh | sh
# Check only, install nothing:
#   curl -fsSL https://raw.githubusercontent.com/fivepeople-art/terminal-setting-kit/main/install.sh | sh -s -- --check
# Safe to run again: each step skips what is already done.
set -eu

REPO="fivepeople-art/terminal-setting-kit"
REF="${TERMINAL_SETTING_REF:-v0.1.8}"
KIT="$HOME/.local/share/terminal-setting-kit"
# The person agrees once, at our own question; Homebrew 7 would ask again in
# English before every install ("Do you want to proceed? [y/n]").
export HOMEBREW_NO_ASK=1

say() { printf '%s\n' "$*"; }
find_brew() {
  for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [ -x "$b" ]; then eval "$("$b" shellenv)"; return 0; fi
  done
  return 1
}

# Everything runs inside main, called on the last line: with `curl | sh` the
# script arrives on stdin, and a command that reads stdin (brew install) would
# otherwise eat the rest of it and end the install early, still exiting 0.
main() {
  [ "$(uname -s)" = Darwin ] || { say "terminal-setting-kit은 macOS에서만 설치됩니다."; exit 1; }
  # curl | sh feeds this script on stdin, so questions are read from the terminal.
  if (exec </dev/tty) 2>/dev/null; then TTY=/dev/tty; else TTY=/dev/null; fi

  CHECK_ONLY=0
  if [ "${1:-}" = "--check" ]; then CHECK_ONLY=1; shift; fi

  # ---- 설치 전 점검: what would stop the install halfway, found before anything is installed.
  blockers=0
  ok() { say "  ✔ $*"; }
  warn() { say "  ! $*"; }
  bad() { say "  ✘ $*"; blockers=$((blockers + 1)); }

  say ""
  say "설치 전 점검"
  version="$(sw_vers -productVersion)"
  major="$(printf '%s' "$version" | cut -d. -f1)"
  if [ "$major" -ge 13 ]; then ok "macOS $version"
  else bad "macOS $version: 13(Ventura) 이상이 필요합니다 → 시스템 설정 > 일반 > 소프트웨어 업데이트에서 올린 뒤 다시 실행"; fi

  if [ "$(uname -m)" = arm64 ]; then ok "Apple 칩 Mac"; else ok "Intel Mac"; fi

  has_brew=0
  if find_brew; then has_brew=1; ok "Homebrew(앱 설치 도구) 있음"
  elif id -Gn | tr ' ' '\n' | grep -qx admin; then ok "관리자 계정(앱 설치 도구를 깔 수 있음)"
  else bad "관리자 계정이 아닙니다: 앱 설치 도구(Homebrew)를 깔 수 없습니다 → 시스템 설정 > 사용자 및 그룹에서 이 계정을 관리자로 바꾸거나 관리자 계정으로 실행"; fi

  # Where this runs from: an agent without a terminal, Herdr itself, SSH, sudo.
  if [ "$(id -u)" = 0 ]; then bad "관리자 권한(sudo)으로 실행했습니다 → sudo 없이 같은 명령을 다시 실행"; fi
  case "${TERM_PROGRAM:-}" in
    herdr) warn "Herdr 안에서 실행 중입니다: 설치하는 동안 단축키와 Herdr 설정이 바로 바뀝니다. 쓰던 설정은 먼저 백업합니다";;
    ghostty) ok "Ghostty에서 실행";;
    Apple_Terminal) ok "터미널 앱에서 실행";;
    *) ok "${TERM_PROGRAM:-터미널}에서 실행";;
  esac
  if [ "$TTY" = /dev/null ]; then
    if [ "$has_brew" = 0 ] || [ ! -d /Applications/Karabiner-Elements.app ]; then
      # An agent may run --check for the person; the install itself still needs them.
      if [ "$CHECK_ONLY" = 1 ]; then
        warn "설치는 비밀번호와 질문 답이 필요해 사람이 직접 합니다: 터미널 앱을 열고 설치 명령(--check 없이)을 붙여 넣기"
      else
        bad "비밀번호를 넣고 질문에 답할 화면이 없습니다(Claude 같은 앱이 대신 실행 중) → 터미널 앱을 열고 같은 명령을 직접 붙여 넣기"
      fi
    else
      warn "질문에 답할 화면이 없어 기본값으로 진행합니다(한/A 짧게 = 한영 전환 켬, 나중에 terminal-setting customize로 바꿈)"
    fi
  fi
  if [ -n "${SSH_CONNECTION:-}" ]; then warn "원격 접속(SSH)입니다: Karabiner 권한 허용과 키 확인은 그 Mac 앞에서 해야 합니다"; fi
  case "$(basename "${SHELL:-zsh}")" in
    zsh|bash) ;;
    *) warn "$(basename "$SHELL") 셸입니다: 새 창에서 terminal-setting 명령이 안 보이면 ~/.local/bin을 PATH에 더하기";;
  esac
  # Same choice as terminal-setting: the first Herdr that is new enough, ~/.local/bin first.
  herdr_ok=""; herdr_old=""
  for h in "$HOME/.local/bin/herdr" "$(command -v herdr 2>/dev/null || true)" /opt/homebrew/bin/herdr /usr/local/bin/herdr; do
    [ -n "$h" ] && [ -x "$h" ] || continue
    hv="$("$h" --version 2>/dev/null | awk '{print $2}')"
    case "$hv" in
      ''|0.[0-8].*|0.9.[0-4]) [ -n "$herdr_old" ] || herdr_old="$hv";;
      *) herdr_ok="$hv"; break;;
    esac
  done
  if [ -n "$herdr_ok" ]; then ok "Herdr ${herdr_ok} 이미 있음(그대로 씁니다)"
  elif [ -n "$herdr_old" ]; then warn "Herdr ${herdr_old}가 있습니다: kit은 0.9.5 이상에서 시험했습니다. 새 판을 ~/.local/bin에 따로 깔고 그것을 씁니다"; fi
  for f in "$HOME/.config/ghostty/config" "$HOME/.config/herdr/config.toml"; do
    if [ -L "$f" ]; then warn "${f}는 다른 곳(dotfiles 등)으로 링크되어 있습니다: 링크를 풀고 kit 파일을 씁니다. 원래 내용은 백업"
    elif [ -e "$f" ]; then warn "쓰던 $(basename "$(dirname "$f")") 설정이 있습니다: 백업하고 kit 설정으로 바꿉니다. 단축키는 kit 것이 되고, 예전 값은 Claude에게 '예전 설정에서 ○○ 가져와줘'로 되살립니다"; fi
  done

  free_kb="$(df -k "$HOME" | awk 'NR==2 {print $4}')"
  if [ "$free_kb" -ge 6000000 ]; then ok "디스크 남은 공간 $((free_kb / 1000000))GB"
  else bad "디스크 남은 공간 $((free_kb / 1000000))GB: 6GB쯤 필요합니다 → 공간을 비운 뒤 다시 실행"; fi

  if curl -fsI --max-time 10 https://github.com >/dev/null 2>&1; then ok "인터넷 연결"
  else bad "GitHub에 연결되지 않습니다 → 인터넷(와이파이·회사 방화벽)을 확인"; fi

  if profiles status -type enrollment 2>/dev/null | grep -q "MDM enrollment: Yes"; then
    warn "회사가 관리하는 Mac입니다: 회사 설정이 키 바꾸기 드라이버(Karabiner)를 막으면 Hyper 키가 안 됩니다. 막히면 회사 IT에 'Karabiner-Elements 드라이버 허용'을 요청"
  else ok "개인 Mac(회사 관리 아님)"; fi

  sources="$(defaults read com.apple.HIToolbox AppleEnabledInputSources 2>/dev/null || true)"
  typing="$(printf '%s\n' "$sources" | grep -c -E 'InputSourceKind = "(Keyboard Layout|Input Mode)"' || true)"
  if printf '%s' "$sources" | grep -q "inputmethod.Korean"; then
    if [ "$typing" -le 2 ]; then ok "입력 소스: 한국어·영어"
    else warn "입력 소스가 ${typing}개입니다: 설치 뒤 한/A를 짧게 누르면 다음 입력 소스로 차례로 넘어갑니다(한·영 둘만 쓰려면 시스템 설정 > 키보드 > 입력 소스에서 나머지를 빼기)"; fi
  else warn "한국어 입력 소스가 없습니다: 한글을 쓰려면 시스템 설정 > 키보드 > 입력 소스에서 '한국어 2벌식'을 추가"; fi

  for app in Ghostty Karabiner-Elements; do
    if [ -d "/Applications/$app.app" ]; then ok "$app 이미 있음(쓰던 설정은 백업한 뒤 바꿉니다)"; fi
  done

  warn "Claude가 명령·파일 작업을 묻지 않고 바로 실행하도록 설정합니다. 되돌리기 어려운 일은 먼저 묻게 하는 몇 줄을 ~/.claude/CLAUDE.md에 더합니다(끄기: terminal-setting set claude-auto-approve off)"
  warn "Claude 유료 계정(Pro·Max·Team·Enterprise)이 필요합니다. 무료 플랜은 Claude Code를 쓸 수 없습니다(설치 뒤 로그인할 때 확인)"
  warn "처음 설치는 20~30분 걸립니다. 전원을 연결해 두세요"

  say ""
  if [ "$blockers" -gt 0 ]; then
    say "✘ ${blockers}개를 고친 뒤 같은 명령을 다시 실행해 주세요. 아무것도 설치하지 않았습니다."
    exit 1
  fi
  if [ "$CHECK_ONLY" = 1 ]; then
    say "점검 통과: 설치할 수 있습니다. ! 표시는 미리 알아 둘 것입니다."
    exit 0
  fi
  if [ "$TTY" = /dev/tty ]; then
    printf '%s' "설치를 시작할까요? [Y/n] "
    read -r answer <"$TTY" || answer=""
    case "$answer" in [nN]*|ㄴ*|아니*) say "설치하지 않았습니다."; exit 0;; esac
  fi

  # ---- 설치
  say ""
  say "terminal-setting-kit 설치를 시작합니다 ($REF). 중간에 끊겨도 같은 명령을 다시 붙여 넣으면 이어서 합니다."

  if [ "$has_brew" = 0 ]; then
    say ""
    say "Homebrew(앱 설치 도구)를 먼저 설치합니다."
    say "  · 'Press RETURN/ENTER to continue'가 나오면 Enter를 누릅니다."
    say "  · Mac 비밀번호를 물으면 입력합니다(입력해도 화면에 글자가 안 보이는 게 정상)."
    say "  · '명령어 라인 개발자 도구를 설치하겠습니까?' 창이 뜨면 '설치'를 누릅니다."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" <"$TTY"
    find_brew || { say "Homebrew 설치를 확인하지 못했습니다. 같은 명령을 다시 실행해 주세요."; exit 1; }
  fi

  [ -x "$(brew --prefix)/bin/python3.14" ] || brew install python@3.14

  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  if [ -n "${TERMINAL_SETTING_SOURCE:-}" ]; then
    cp -R "$TERMINAL_SETTING_SOURCE" "$tmp/kit"
  else
    curl -fsSL "https://codeload.github.com/$REPO/tar.gz/refs/tags/$REF" -o "$tmp/kit.tar.gz"
    mkdir "$tmp/kit"
    tar -xzf "$tmp/kit.tar.gz" -C "$tmp/kit" --strip-components 1
  fi
  mkdir -p "$(dirname "$KIT")" "$HOME/.local/bin"
  rm -rf "$KIT.new"
  mv "$tmp/kit" "$KIT.new"
  rm -rf "$KIT"
  mv "$KIT.new" "$KIT"
  chmod +x "$KIT/bin/terminal-setting"
  ln -sf "$KIT/bin/terminal-setting" "$HOME/.local/bin/terminal-setting"

  exec "$KIT/bin/terminal-setting" install "$@" <"$TTY"
}

main "$@"

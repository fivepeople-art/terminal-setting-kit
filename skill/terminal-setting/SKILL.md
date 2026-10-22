---
name: terminal-setting
description: >
  Guide and fix this Mac's terminal setup (Ghostty + Herdr + Hyper key,
  installed by terminal-setting-kit): teach the keys, customize font size, look,
  shortcuts, Hyper key and themes ("글자 크게", "사이드바 넓게"), diagnose
  "Hyper 키가 안 돼", "터미널 점검해줘", "단축키 바꿔줘", "테마 바꿔줘",
  "업데이트해줘", "처음 사용법 알려줘", "terminal-setting", and remove it.
---

# terminal-setting

이 Mac의 터미널 환경은 terminal-setting-kit이 깔았다. 화면은 Ghostty(터미널 앱) 안의
Herdr(에이전트 여러 개를 나란히 띄우는 작업 창)이고, Karabiner가 Hyper 키
(Ctrl+Option+Command를 한 키로)를 만든다. 사용자는 대개 개발자가 아니다:
명령은 직접 실행하고, 결과는 쉬운 말로 짧게 알린다.

## 명령 하나: `terminal-setting`

| 하고 싶은 것 | 명령 |
|---|---|
| 점검(무엇이 고장났나) | `terminal-setting doctor` |
| 설치 뒤 확인 순서 | `terminal-setting guide` |
| 바꿀 수 있는 것과 지금 값 | `terminal-setting settings` |
| 하나 바꾸기 / 되돌리기 | `terminal-setting set 이름 값` / `terminal-setting unset 이름` |
| 단축키 바꾸기·끄기·되돌리기 | `terminal-setting key 동작 hyper+y` / `… off` / `… default` |
| 단축키 표 | `terminal-setting keys` (기계용 `--json`) |
| 테마 | `terminal-setting theme list`, `terminal-setting theme <이름>`, `terminal-setting theme cycle` |
| 사람이 직접 고르는 메뉴 | `terminal-setting customize` (Claude가 대신 할 때는 위 명령을 쓴다) |
| 모두 기본값으로 | `terminal-setting reset` (먼저 묻는다) |
| 새 판 받기 / 이어서 설치 | `terminal-setting update` / `terminal-setting install` |
| 지우고 되돌리기 | `terminal-setting uninstall` (사용자에게 먼저 묻는다) |

## 꾸미기: 사용자가 말하면 명령으로 바꾼다

사용자는 파일을 열지 않는다. "글자 좀 크게", "사이드바 넓게", "알림 꺼 줘", "테마 바꿀 단축키를 Hyper+Y로"처럼 말하면 맞는 명령을 실행하고, 무엇이 바뀌었는지와 되돌리는 말("원래대로 해줘")을 한 줄로 알린다. 모든 선택은 사용자 파일 `~/.config/terminal-setting/settings.toml` 하나에 남고 업데이트가 건드리지 않는다. 바꾸기가 실패하면 파일은 그대로이고 이유가 나온다(범위 밖 값, 겹치는 단축키 등): 그 이유를 쉬운 말로 전한다.

| 사용자 말 | 이름 | 값 |
|---|---|---|
| 글자 크기 | `font-size` | 8~40 (기본 16) |
| 글꼴 | `font` | Mac에 깔린 글꼴 이름 (기본 Geist Mono, 한글은 Apple SD Gothic Neo가 받침) |
| 창 투명하게 | `opacity` | 0.3~1.0 |
| 커서 모양 | `cursor` | block / bar / underline |
| 창 여백 | `padding` | 0~40 |
| 사이드바 너비 | `sidebar-width` | 12~30 |
| 닫기 전에 묻기 | `confirm-close` | on / off |
| 알림 방식 | `notifications` | herdr(창 안) / system(macOS 알림) / terminal / off |
| Hyper 키 | `hyper-key` | caps_lock(한/A) / right_option(오른쪽 Option) |
| 한/A 짧게 = 한영 | `hangul-tap` | on / off |

- 표에 없는 Ghostty·Herdr 설정은 원래 이름으로: `terminal-setting set ghostty.window-padding-y 12`, `terminal-setting set herdr.ui.pane_gaps true`. 값이 맞는지는 Ghostty·Herdr 공식 문서(`herdr --default-config`)로 먼저 확인한다. Herdr `keys`·`theme` 표와 Ghostty `keybind`·`theme`은 kit이 만든다: 단축키는 `key`, 테마는 `theme`으로.
- 동작 이름은 `terminal-setting keys`의 대괄호 안. 키는 `hyper+t`, `cmd+up`처럼. 탭 번호(Cmd+1~9)와 macOS 키(Cmd+C·V·Q·W 등)는 못 바꾼다.
- 같은 이름을 여러 번 쓰는 Ghostty 설정(keybind 등)이나 복잡한 것은 `~/.config/ghostty/local`에 줄로 쓴다(기본 설정 위에 덮어씀, 저장하면 Ghostty가 다시 읽음).
- 사용자가 kit 파일(`~/.config/ghostty/config`, `~/.config/herdr/config.toml`)을 손으로 고쳤어도 잃지 않는다: 다음 apply·update가 바뀐 줄을 `ghostty/local`과 settings.toml로 옮기고 알린다. 옮기지 못한 것(Herdr 단축키·목록)은 `~/.local/state/terminal-setting/backups/`에 남는다.

## 설치·업데이트를 대신 해 달라고 할 때

- **처음 설치**는 사용자가 터미널 앱에 직접 붙여 넣어야 한다: Mac 비밀번호와 Karabiner 권한 허용은 이 세션이 대신 못 한다. 점검만은 대신 돌려도 된다(`… | sh -s -- --check`, 비밀번호 없음). 설치 명령은 README 첫 줄.
- **`terminal-setting update`·`apply`·`set`**은 대신 실행해도 된다(비밀번호 없음). 새 판이 Karabiner나 앱을 새로 깔아야 하면 그 단계만 사용자에게 터미널에서 `terminal-setting install`을 부탁한다.

## 원래 Ghostty·Herdr를 쓰던 사람

설치가 쓰던 `~/.config/ghostty/config`·`~/.config/herdr/config.toml`을 `~/.local/state/terminal-setting/backups/<날짜>/`에 보관하고 kit 것으로 바꿨다(단축키는 kit 것). "예전 설정에서 글자 크기 가져와줘"처럼 말하면 그 백업을 읽어, 원하는 값만 `terminal-setting set`(표의 이름 또는 `ghostty.이름`·`herdr.표.이름`)이나 `~/.config/ghostty/local`로 옮긴다. 예전 keybind·Herdr 단축키를 통째로 되살리면 kit 단축키와 부딪히니, 한 동작씩 `terminal-setting key`로 옮긴다. 쓰던 Herdr가 0.9.5보다 오래됐으면 kit이 새 판을 `~/.local/bin`에 따로 깔았다: 옛 Herdr 창은 닫고 Ghostty 새 창에서 연다.

## 고장 진단 순서

1. `terminal-setting doctor`를 돌리고 ✘ 줄의 → 안내대로 고친다.
2. **Hyper 키가 아무 데서도 안 먹음**: Karabiner 권한이다. 시스템 설정 > 개인정보 보호 및 보안 > 입력 모니터링에서 `karabiner_grabber`·`Karabiner-Core-Service` 켜기, 시스템 설정 > 일반 > 로그인 항목 및 확장 프로그램 > 드라이버 확장 프로그램에서 Karabiner 켜기. 사용자가 직접 눌러야 한다: 어디를 누르는지 한 단계씩 말한다.
3. **Hyper는 되는데 Herdr 단축키만 안 됨**: `herdr config check`, 그다음 `terminal-setting apply`. Herdr 안이 아니면(`HERDR_ENV`가 1이 아님) Ghostty를 새로 열면 Herdr가 뜬다.
4. **한/A 짧게 눌러도 한영이 안 바뀜**: `terminal-setting settings`에서 hangul-tap이 켬인지(아니면 `terminal-setting set hangul-tap on`), 시스템 설정 > 키보드 > 키보드 단축키 > 입력 소스의 "입력 메뉴에서 다음 소스 선택"이 F18인지 본다. 아니면 `terminal-setting apply`. 1초 넘게 누르고 떼면 바뀌지 않는 것이 정상이다.
5. **대문자 고정이 안 됨**: 한/A가 Hyper라서 대문자 고정은 Shift+한/A다(`hyper = "caps_lock"`일 때).
6. 업데이트 뒤 이상하면 `terminal-setting doctor`, 그래도 안 되면 backups 폴더의 직전 파일과 비교한다.

## 처음 쓰는 사람과 함께 할 것

먼저 `terminal-setting guide`로 그 사람 설정에 맞는 확인 순서를 받아, 한 번에 하나씩 해 보게 하고 "됐어요/안 돼요"를 듣는다. 안 되면 그 단계에 적힌 고치는 법부터, 그다음 `terminal-setting doctor`. 다 되면 짧게 알려 준다:

1. 창 하나에 여러 칸(pane)을 두고, 칸마다 Claude 같은 에이전트를 띄운다. 왼쪽 사이드바가 스페이스와 에이전트 상태(일함·기다림·끝남)를 보여 준다.
2. 먼저 익힐 키 다섯: 칸 나누기, 칸 사이 이동, 에이전트 사이 이동, 새 탭, 단축키 도움말. 실제 키는 `terminal-setting keys`로 확인해 그 사람 설정대로 말한다.
3. 글자 크기·단축키·테마 등 무엇이든 "바꿔줘"라고 말하면 된다. 직접 고르고 싶으면 `terminal-setting customize`.
4. 막히면 언제든 Claude에게 "터미널 점검해줘".

## 설치 전 점검

설치 명령은 먼저 점검만 할 수 있다: `curl -fsSL https://raw.githubusercontent.com/fivepeople-art/terminal-setting-kit/main/install.sh | sh -s -- --check`. macOS 13 이상, 관리자 계정, 디스크 6GB, 인터넷을 막는 것(✘)으로, 회사 관리 Mac·입력 소스 셋 이상·Claude 유료 계정을 미리 알 것(!)으로 보인다. ✘가 있으면 아무것도 깔지 않는다.

## Herdr 자체를 다룰 때

Herdr 공식 스킬(`herdr`)이 함께 깔려 있다. pane·탭·에이전트를 명령으로 다룰 때는 그 스킬을 따른다.

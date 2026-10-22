---
name: terminal-setting
description: >
  Guide and fix this Mac's terminal setup (Ghostty + Herdr + Hyper key,
  installed by terminal-setting-kit): teach the keys, customize font size, look,
  shortcuts, Hyper key and themes ("글자 크게", "사이드바 넓게"), diagnose
  "Hyper 키가 안 돼", "터미널 점검해줘", "단축키 바꿔줘", "테마 바꿔줘",
  "한영이 이상해", "외장 키보드", "이 Mac에 맞춰줘", "업데이트해줘",
  "처음 사용법 알려줘", "terminal-setting", and remove it.
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
| 이 Mac 정보(키보드·입력 소스·화면 언어·겹치는 앱) | `terminal-setting env` (기계용 `--json`) |
| 설치 뒤 확인 순서 | `terminal-setting guide` |
| 바꿀 수 있는 것과 지금 값 | `terminal-setting settings` |
| 하나 바꾸기 / 되돌리기 | `terminal-setting set 이름 값` / `terminal-setting unset 이름` |
| 설정 파일을 다시 적용(손으로 고친 뒤 등) | `terminal-setting apply` |
| 단축키 바꾸기·끄기·되돌리기 | `terminal-setting key 동작 hyper+y` / `… off` / `… default` |
| 단축키 표 | `terminal-setting keys` (기계용 `--json`) |
| 테마 | `terminal-setting theme list`, `terminal-setting theme "Eyes Night"`, `terminal-setting theme cycle` |
| 사람이 직접 고르는 메뉴 | `terminal-setting customize` (사람이 터미널에서 쓰는 것. Claude는 위 명령을 쓴다) |
| 모두 기본값으로 | 사용자에게 묻고 "응"이면 `terminal-setting reset --yes` |
| 새 판 받기 / 이어서 설치 | `terminal-setting update` / `terminal-setting install`(사용자가 터미널에서) |
| 지우고 되돌리기 | 사용자에게 묻고 "응"이면 `terminal-setting uninstall --yes` |

`reset`·`uninstall`은 이 세션처럼 답할 화면이 없으면 `--yes` 없이는 아무것도 하지 않고 그렇게 말한다. 그 말을 "됐다"로 전하지 않는다.

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
| Claude가 묻지 않고 실행 | `claude-auto-approve` | on(기본) / off: off면 명령·파일 작업 전에 허락을 묻는다 |
| 답변 방식 | `reply-style` | i-have-adhd(기본, 결론 먼저·쉬운 말) / default(Claude 기본) |

- 표에 없는 Ghostty·Herdr 설정은 원래 이름으로: `terminal-setting set ghostty.window-padding-y 12`, `terminal-setting set herdr.ui.pane_gaps true`. 값이 맞는지는 Ghostty·Herdr 공식 문서(`herdr --default-config`)로 먼저 확인한다. Herdr `keys`·`theme` 표와 Ghostty `keybind`·`theme`은 kit이 만든다: 단축키는 `key`, 테마는 `theme`으로.
- 동작 이름은 `terminal-setting keys`의 대괄호 안. 키는 `hyper+t`, `cmd+up`처럼. 탭 번호(Cmd+1~9)와 macOS 키(Cmd+C·V·Q·W 등)는 못 바꾼다.
- 원하는 키를 이미 다른 동작이 쓰면 `key`가 "X와 Y가 같은 키입니다"라며 멈춘다. 그 키를 가진 동작을 쉬운 이름(`keys`의 설명)으로 말하고 고르게 한다: 그 동작을 다른 키로 옮기거나 끈 뒤(`terminal-setting key pane_resize_up hyper+…` 또는 `… off`) 원래 바꾸려던 것을 바꾼다. 빈 키는 `terminal-setting keys`에 없는 글자다.
- 같은 이름을 여러 번 쓰는 Ghostty 설정(keybind 등)이나 복잡한 것은 `~/.config/ghostty/local`에 줄로 쓴다(기본 설정 위에 덮어씀, 저장하면 Ghostty가 다시 읽음).
- 사용자가 kit 파일(`~/.config/ghostty/config`, `~/.config/herdr/config.toml`)을 손으로 고쳤어도 잃지 않는다: 다음 apply·update가 바뀐 줄을 `ghostty/local`과 settings.toml로 옮기고 알린다. 옮기지 못한 것(Herdr 단축키·목록)은 `~/.local/state/terminal-setting/backups/`에 남는다.

## 이 Mac에 맞추기

Mac마다 키보드·입력 소스·화면 언어·함께 쓰는 앱이 다르다. 맞춰 달라는 말이나 "안 돼요"를 들으면 먼저 `terminal-setting env`를 돌려 사실을 보고(! 줄이 겹침·주의), 아래에서 맞는 줄을 고른다. 추측으로 설정을 바꾸지 않는다.

| 이 Mac의 상황 | 할 일 |
|---|---|
| 화면 언어가 영어(`ui_language`가 en…) | 시스템 설정 길을 영어로 말한다: 시스템 설정=System Settings, 개인정보 보호 및 보안=Privacy & Security, 입력 모니터링=Input Monitoring, 손쉬운 사용=Accessibility, 키보드=Keyboard, 키보드 단축키=Keyboard Shortcuts, 입력 소스=Input Sources, 보조 키=Modifier Keys, 알림=Notifications |
| 이름을 헷갈리기 쉬운 것 | Hyper 키 바꾸기는 `set hyper-key …`(파일 안 이름 `hyper`가 아니다), `padding`은 좌우 여백만(위아래는 `ghostty.window-padding-y`) |
| 한/영 키가 따로 있는 키보드(PC용 한국어 키보드 등) | 한/A는 Hyper로만 쓰고 한영은 그 키로: `terminal-setting set hangul-tap off` |
| Caps Lock을 대문자로 자주 쓰거나 한/A를 건드리기 싫다 | Hyper를 오른쪽 Option으로: `terminal-setting set hyper-key right_option`(대문자 고정은 원래대로 한/A) |
| Windows용 외장 키보드 | Alt 자리가 Option, Windows 키 자리가 Command다. macOS 보조 키 설정은 Karabiner가 도는 동안 무시된다(Karabiner 설명서). 로지텍 키보드 다수는 Fn+O를 3초 눌러 Mac 배열로 바뀐다(키보드 설명서 확인). 아니면 Karabiner-Elements > Simple Modifications에서 그 키보드를 고르고 left_option↔left_command를 맞바꾼다 |
| 기호가 키보드 글자와 다르게 찍힘(` ₩ § 등) | Karabiner-Elements > Virtual Keyboard에서 키보드 종류(ANSI·ISO·JIS)를 쓰는 키보드와 같게 고른다. 한국어 입력일 때 `가 ₩로 찍히는 것은 macOS 한글 자판의 원래 동작이다 |
| 입력 소스가 셋 이상(일본어·중국어 등)이거나 세벌식·구름 입력기 | 한/A 짧게가 "다음 입력 소스"로 차례로 넘긴다(한→영→일→한). 쓰는 소스는 빼라고 하지 않는다: 한/A를 한 번 더 누르면 다음 소스로 간다고 알리고(메뉴 막대의 입력 메뉴에서 바로 골라도 된다), 정말 안 쓰는 소스만 빼자고 권한다. 세벌식·구름도 입력 소스 하나로 세므로 그대로 된다 |
| Hyper 키를 Karabiner Simple Modifications에서 다른 키로 바꿔 둠(env의 !) | 그 줄이 kit 규칙보다 먼저 적용돼 Hyper가 안 된다. 쓰지 않으면 Karabiner-Elements > Simple Modifications에서 그 줄을 지운다. macOS 시스템 설정의 보조 키 설정은 Karabiner가 도는 동안 무시되니 거기서 고치라고 하지 않는다 |
| Raycast Hyper Key | 끄라고 하기 전에 Raycast에 Hyper 단축키를 녹음해 두었는지 묻는다(Raycast의 Hyper는 Shift까지 넣을 수 있어 kit의 Hyper와 다른 키가 된다). 쓰고 있으면 kit Hyper를 오른쪽 Option으로 옮기거나(`set hyper-key right_option`, Raycast는 한/A 그대로), Raycast 단축키를 `terminal-setting keys`에 없는 Hyper+키로 다시 녹음한 뒤 Raycast 설정 > Advanced > Hyper Key를 끈다 |
| BetterTouchTool·Hammerspoon·Keyboard Maestro 등 | 같은 키를 두 앱이 잡으면 한쪽만 먹는다. 그 앱에서 겹치는 단축키를 지우거나 `terminal-setting key`로 우리 쪽을 옮긴다 |
| 글자가 작다·크다 | 지금 값(`terminal-setting settings`, 기본 16)에서 2씩 올리거나 내린다(작다면 18→20). 작은 노트북 화면에 칸을 더 넣고 싶다는 말일 때만 14를 권하고, 그때는 사이드바도 `sidebar-width 16` |
| "다크 모드로" | macOS 전체를 말하는지 터미널만인지 먼저 묻는다. 터미널이면 Eyes Day=밝은 크림, fapibrown=어두운 갈색, Eyes Night=어두운 초록 중 고르게 하고 `terminal-setting theme "Eyes Night"`(띄어쓰기 있는 이름은 따옴표). macOS 전체면 시스템 설정 > 화면 모드 |
| 글꼴을 바꿔 달라 | 먼저 깔려 있는지: `/Applications/Ghostty.app/Contents/MacOS/ghostty +list-fonts | grep -i d2coding`. 없으면 깔지 먼저 묻고(앱 설치) `brew install --cask font-d2coding`(이름은 `brew search font-`로 찾음), 그다음 `terminal-setting set font "D2Coding"`(목록에 나온 이름 그대로) |
| Claude가 기다려도 알림이 안 뜸 | 시스템 설정 > 알림 > Ghostty에서 알림 허용 |
| 설정을 바꿔도 Ghostty가 그대로 | Ghostty에서 Cmd+Shift+,(다시 읽기). 매번 그렇다면 시스템 설정 > 개인정보 보호 및 보안 > 자동화에서 Ghostty 제어를 허용 |
| 회사가 관리하는 Mac | 확인: `profiles status -type enrollment`에 "MDM enrollment: Yes". Karabiner 드라이버가 막히면 한/A·오른쪽 Option 어느 쪽도 Hyper가 안 된다(둘 다 Karabiner가 만든다). 허용을 기다리는 동안은 Ctrl+Option+Command를 손으로 함께 누르면 Hyper 단축키가 된다. 회사 IT에 보낼 문구를 써 준다: "Karabiner-Elements(pqrs.org, 개발자 Team ID G43BCU2T37)의 드라이버 확장(org.pqrs.Karabiner-DriverKit-VirtualHIDDevice)과 입력 모니터링·손쉬운 사용 권한을 허용해 주세요" |

## 이 Claude가 묻지 않고 실행하는 것

kit이 Claude 권한 방식을 "묻지 않고 실행"(`bypassPermissions`)으로 두었다(사용자가 원래 정해 둔 값이 없을 때만). 그래서 파일 삭제·덮어쓰기, 앱 설치, 밖으로 보내는 일(메일·게시·결제)처럼 되돌리기 어려운 일은 실행 전에 한 줄로 무엇을 할지 말하고 사용자의 "응"을 받는다. 사용자가 무섭다거나 매번 묻게 하고 싶다고 하면 `terminal-setting set claude-auto-approve off`를 실행하고, 지금 이 Claude는 그대로라는 것을 알린다: 이 창을 끝내고(/exit) 새로 열면 그때부터 묻는다. 그때까지 이 세션은 무엇이든 실행 전에 묻는다.

## 설치·업데이트를 대신 해 달라고 할 때

- **처음 설치**는 사용자가 터미널 앱에 직접 붙여 넣어야 한다: Mac 비밀번호와 Karabiner 권한 허용은 이 세션이 대신 못 한다. 점검만은 대신 돌려도 된다(`… | sh -s -- --check`, 비밀번호 없음). 설치 명령은 README 첫 줄.
- **`terminal-setting update`·`apply`·`set`**은 대신 실행해도 된다(비밀번호 없음). `update`는 새 판의 설정·plugin·Claude 연결까지 맞추고 끝에 점검을 보인다. ✘에 `terminal-setting install`이 나오면 그 단계는 앱 설치라 사용자에게 터미널(Herdr pane)에서 직접 실행해 달라고 한다.
- 앱 자체(Ghostty·Karabiner)의 새 판은 kit 업데이트와 별개다: `brew upgrade --cask ghostty karabiner-elements`. 앱 설치라 먼저 묻는다. Herdr는 `herdr update`.

## 원래 Ghostty·Herdr를 쓰던 사람

설치가 쓰던 `~/.config/ghostty/config`·`~/.config/herdr/config.toml`을 백업하고 kit 것으로 바꿨다(단축키는 kit 것). 백업은 `~/.local/state/terminal-setting/backups/<YYYYMMDD-HHMMSS>/` 아래 홈 기준 같은 경로(예: `…/backups/20261022-153000/.config/ghostty/config`)에 있다. `.config`가 숨은 폴더라 그냥 보면 빈 폴더 같으니 `find ~/.local/state/terminal-setting/backups -type f`로 찾는다. 전부 설치 전으로 되돌리는 길은 uninstall이다. "예전 설정에서 글자 크기 가져와줘"처럼 말하면 그 백업을 읽어, 원하는 값만 `terminal-setting set`(표의 이름 또는 `ghostty.이름`·`herdr.표.이름`)이나 `~/.config/ghostty/local`로 옮긴다. 예전 keybind·Herdr 단축키를 통째로 되살리면 kit 단축키와 부딪히니, 한 동작씩 `terminal-setting key`로 옮긴다. 쓰던 Herdr가 0.9.5보다 오래됐으면 kit이 새 판을 `~/.local/bin`에 따로 깔았다: 옛 Herdr 창은 닫고 Ghostty 새 창에서 연다.

## 고장 진단 순서

1. `terminal-setting doctor`를 돌리고 ✘ 줄의 → 안내대로 고친다.
2. **Hyper 키가 아무 데서도 안 먹음**: 대개 Karabiner 권한이다. Karabiner는 넷이 필요하다: 백그라운드 서비스, 손쉬운 사용, 입력 모니터링, 드라이버 확장 프로그램. 사용자에게 Karabiner-Elements 앱을 열게 하면 창이 남은 허용을 위에서부터 보여 주고 버튼이 맞는 시스템 설정 화면을 연다(macOS 판마다 화면 위치가 달라 그 안내를 따르는 게 정확하다). 사용자가 직접 눌러야 하니 한 단계씩 말한다. 권한이 다 됐는데도 안 되면 `terminal-setting env`의 ! 줄(Karabiner Simple Modifications, 겹치는 앱)을 본다.
3. **Hyper는 되는데 Herdr 단축키만 안 됨**: `herdr config check`, 그다음 `terminal-setting apply`. Herdr 안이 아니면(`HERDR_ENV`가 1이 아님) Ghostty를 새로 열면 Herdr가 뜬다.
4. **한/A 짧게 눌러도 한영이 안 바뀜**: `terminal-setting settings`에서 hangul-tap이 켬인지(아니면 `terminal-setting set hangul-tap on`), `terminal-setting doctor`의 "한영 전환 단축키 F18" 줄이 ✔인지 본다(✘면 `terminal-setting apply`). 1초 넘게 누르고 떼면 바뀌지 않는 것이 정상이다. 입력 소스가 셋 이상이면 바뀌는 게 아니라 다음 소스로 넘어가는 것이니 위 "이 Mac에 맞추기"를 본다.
5. **대문자 고정이 안 됨**: 한/A가 Hyper일 때(hyper-key가 caps_lock) 대문자 고정은 Shift+한/A다.
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

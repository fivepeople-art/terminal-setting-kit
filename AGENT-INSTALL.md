# terminal-setting-kit 설치: AI 에이전트용 절차

사람이 AI 에이전트(Claude Code, Codex 등)에게 이 문서를 주며 설치를 맡겼다. 이 문서대로 Mac을 살피고, 점검하고, 사람이 할 일을 한 번에 하나씩 안내하고, 설치 뒤 확인과 기록까지 마친다. 중간에 대화가 끊겨 새 에이전트가 이 문서를 다시 받아도 0단계가 지금 위치를 찾아 이어 간다.

사람은 대개 개발자가 아니다. 결과는 쉬운 말로 짧게 알리고, 사람이 할 일은 한 번에 하나만 말하고 "됐어요"를 기다린다. 무엇을 하는지는 README가 설명한다: https://raw.githubusercontent.com/fivepeople-art/terminal-setting-kit/main/README.md

## 사람만 할 수 있는 것

에이전트는 아래 셋을 대신하지 않는다. 언제 무엇을 누를지 알려 주기만 한다.

- **설치 명령 실행**: Mac 비밀번호, Homebrew의 Enter, 설치 중 질문 하나("한/A 키로 한영을 바꾸세요?")가 필요하다. 사람이 Mac 기본 **터미널** 앱에 직접 붙여 넣는다.
- **Karabiner 권한 허용**: 시스템 설정에서 사람이 눌러야 한다(백그라운드 서비스, 손쉬운 사용, 입력 모니터링, 드라이버 확장 프로그램).
- **Claude 로그인**: 처음 `claude`를 실행하면 브라우저에서 한다(Claude Pro 이상 계정, 무료 플랜은 Claude Code가 안 된다).

## 0. 지금 어디인가

1. macOS가 아니면 이 kit은 안 된다고 알리고 멈춘다(`uname -s`가 Darwin).
2. `~/.local/bin/terminal-setting`이 있으면 이미 설치된 Mac이다. `~/.local/bin/terminal-setting --version`으로 판을 보고, 사람에게 묻고 `terminal-setting update`를 실행한 뒤 5단계로 간다.
3. `~/terminal-setting-before.md`가 있으면 앞선 에이전트가 2단계를 해 둔 것이다. 읽고 이어 쓴다.
4. 둘 다 없으면 1단계부터 한다.

## 1. 점검(아무것도 설치하지 않는다)

```sh
curl -fsSL https://raw.githubusercontent.com/fivepeople-art/terminal-setting-kit/main/install.sh | sh -s -- --check
```

- ✔는 됨, !는 알아 둘 것, ✘는 고쳐야 할 것이다. 줄마다 → 뒤에 고치는 법이 있다.
- 에이전트가 돌리면 "설치는 … 사람이 직접 합니다" !가 나오는 게 정상이다.
- ✘가 있으면 사람에게 하나씩 고치게 안내하고(관리자 계정, macOS 판, 디스크 등) 다시 점검한다. ✘가 없어질 때까지 3단계로 가지 않는다.
- ! 줄 가운데 사람이 알아야 할 것(회사 관리 Mac, 입력 소스 셋 이상, Claude 자동 실행 설정)은 쉬운 말로 전한다.

## 2. 지금 쓰는 설정 지키기

설치는 아래 파일을 백업한 뒤 kit 것으로 바꾼다. 단축키도 kit 것이 된다. 그 전에 사람이 바꿔 둔 값을 적어 둔다.

- `~/.config/ghostty/config`(또는 `config.ghostty`), `~/.config/herdr/config.toml`이 있으면 읽고, 사람이 정한 것으로 보이는 값(글자 크기, 글꼴, 테마, 투명도, 여백, 직접 정한 단축키, Herdr 사이드바 등)을 `~/terminal-setting-before.md`에 목록으로 저장한다. 파일이 다른 곳(dotfiles 등)으로 연결된 링크면 그 사실도 적는다.
- `~/.config/karabiner/karabiner.json`이 있으면 기존 규칙 이름만 적는다. kit은 자기 규칙(`terminal-setting:`로 시작)만 넣고 빼며 나머지는 건드리지 않는다.
- 목록을 보여 주고 설치 뒤 무엇을 되살릴지 사람에게 묻고, 답을 같은 파일에 적는다.
- 위 파일이 하나도 없으면 "지킬 설정 없음"이라고만 적고 넘어간다.

## 3. 설치(사람이 한다)

사람에게 아래를 하나씩 안내한다. 에이전트는 이 명령을 실행하지 않는다.

1. Mac 기본 **터미널** 앱을 연다(Spotlight에서 "터미널"). Ghostty·Herdr 안에서는 실행하지 않는다: 설치하는 동안 그 화면의 설정과 단축키가 바뀐다.
2. 붙여 넣고 Enter:

   ```sh
   curl -fsSL https://raw.githubusercontent.com/fivepeople-art/terminal-setting-kit/main/install.sh | sh
   ```

3. 나올 수 있는 것(모두 정상): "Press RETURN/ENTER" → Enter, 비밀번호(쳐도 안 보임), "명령어 라인 개발자 도구 설치" → 설치, "인터넷에서 다운로드한 앱" → 열기, "백그라운드 항목이 추가됨" → 그대로, "Ghostty을(를) 제어하려고 합니다" → 허용, Karabiner 창 → 안내대로 위에서부터 허용(키보드 종류를 물으면 쓰는 키보드와 같은 것, Apple 한국어 키보드는 보통 ANSI).
4. 끊기면 같은 명령을 다시 붙여 넣으면 이어서 한다.
5. 끝나면 설치가 Ghostty를 연다. Ghostty가 설치 전부터 열려 있었으면 Cmd+Q로 완전히 닫고 다시 연다(열려 있던 창은 예전 Herdr 그대로다). 걸린 시간을 기억해 달라고 한다.

이 대화가 Ghostty 안에서 돌고 있으면 5에서 끊길 수 있다. 그 전에 사람에게 알린다: "다시 열고 새 에이전트에게 처음 받은 한 줄을 그대로 주세요. 이어서 합니다."

## 4. 설치가 끝났는지 확인

`~/.local/bin/terminal-setting --version`이 나오면 끝났다. 안 나오면 터미널 앱 화면의 마지막 줄들을 사람에게 받아(캡처 가능) 어디서 멈췄는지 보고, 같은 설치 명령을 다시 붙여 넣게 한다.

## 5. 설치 뒤

설치가 `~/.claude/skills/terminal-setting/SKILL.md`(터미널 고장 진단·꾸미기 안내)를 깐다. 여기서부터는 그 스킬을 함께 따른다.

1. `terminal-setting doctor`를 돌리고 ✘ 줄의 → 안내대로 하나씩 고친다. Hyper 키가 안 되면 대개 Karabiner 권한이다: Karabiner-Elements 앱을 열게 하고 창의 안내를 위에서부터 따르게 한다.
2. `~/terminal-setting-before.md`에서 되살리기로 한 값을 옮긴다: 흔한 값은 `terminal-setting set 이름 값`(이름 목록은 `terminal-setting settings`), 단축키는 `terminal-setting key 동작 키`(동작 목록은 `terminal-setting keys`), 그 밖의 Ghostty 설정은 `~/.config/ghostty/local`에 한 줄씩. 원래 파일 백업은 `~/.local/state/terminal-setting/backups/`에 있다. 예전 단축키를 통째로 되살리지 말고 한 동작씩 옮긴다(kit 단축키와 부딪힌다).
3. `terminal-setting guide`가 보여 주는 순서대로 사람과 하나씩 확인한다: 한/A 짧게 누르기(한영 전환), 한/A 누른 채 다른 키(Hyper 단축키), Shift+한/A(대문자 고정), Claude 로그인. 안 되는 것은 스킬의 "고장 진단 순서"를 따른다.
4. 앞으로는 "글자 크게 해줘", "테마 바꿔줘", "단축키 바꿔줘"처럼 Claude에게 말하면 된다고 알린다.

## 6. 기록

`~/terminal-setting-report.md`에 남기고 사람에게 보여 준다:

- 날짜, kit 판(`terminal-setting --version`), macOS 판, 칩(Apple/Intel), 걸린 시간
- 점검의 !·✘ 줄과 고친 방법
- 막히거나 헷갈린 곳(어느 단계, 무엇이 보였나)
- `terminal-setting doctor` 결과, 키 확인 결과
- 되살린 설정과 못 되살린 것

고칠 점이 있었으면 GitHub 이슈 문안을 써 준다(https://github.com/fivepeople-art/terminal-setting-kit/issues/new). 올릴지는 사람이 정한다. 이 kit을 건네준 사람에게 보내 달라는 부탁을 받았다면 이 기록이 그 보고다.

## 지킬 것

- `sudo`로 실행하지 않는다(설치가 멈춘다).
- 설치 명령(`--check` 없이)은 사람이 터미널 앱에서 실행한다. 에이전트가 화면 없이 실행하지 않는다.
- `~/.local/state/terminal-setting/backups/`와 `~/terminal-setting-before.md`는 지우지 않는다.
- `~/.config/ghostty/config`, `~/.config/herdr/config.toml`은 직접 고치지 않는다. `terminal-setting` 명령과 `~/.config/ghostty/local`을 쓴다.
- `~/.claude/CLAUDE.md`의 `terminal-setting >>>` 구역은 kit이 관리한다. 고치지 않는다.
- `terminal-setting reset`·`uninstall`은 사람이 분명히 원할 때만, 묻고 실행한다.

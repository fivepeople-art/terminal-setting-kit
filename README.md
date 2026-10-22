# terminal-setting-kit

AI 에이전트 여러 개를 한 화면에 나란히 띄워 일하는 Mac 터미널 환경입니다.
Ghostty(터미널 앱) 안에서 Herdr(에이전트 작업 창)이 열리고, 한/A 키 하나로 단축키(Hyper 키)를 씁니다.
Claude Code가 함께 깔리고, 막히면 Claude에게 물으면 됩니다.

## 설치 전에 확인할 것

- **Mac**: macOS 13(Ventura) 이상, 디스크 6GB 이상, 이 Mac의 **관리자 계정**(앱 설치 도구가 비밀번호를 묻습니다). 설치 프로그램이 처음에 확인하고, 안 맞으면 무엇을 고칠지 알려 줍니다.
- **Claude 유료 계정**: Claude Code는 Pro·Max·Team·Enterprise 계정에서만 됩니다(무료 플랜은 안 됨).
- **회사 Mac**: 회사가 관리하는 Mac이면 키 바꾸기 드라이버(Karabiner)가 막힐 수 있습니다. 개인 Mac을 권합니다.
- **입력 소스**: 한/A로 한영을 바꾸던 분은 그대로 됩니다. 입력 소스가 셋 이상(예: 일본어 추가)이면 한/A가 다음 입력 소스로 차례로 넘어갑니다.
- **시간**: 처음이면 20~30분. 전원을 연결해 두세요.

설치 명령이 처음에 이것들을 스스로 점검하고(✔ 됨, ! 알아 둘 것, ✘ 고쳐야 함), ✘가 있으면 아무것도 깔지 않고 고칠 곳을 알려 줍니다. 점검만 먼저 해 보려면:

```sh
curl -fsSL https://raw.githubusercontent.com/fivepeople-art/terminal-setting-kit/main/install.sh | sh -s -- --check
```

## 설치

1. **터미널** 앱을 엽니다(Spotlight에서 "터미널" 검색).
2. 아래 한 줄을 복사해 붙여 넣고 Enter를 누릅니다.

   ```sh
   curl -fsSL https://raw.githubusercontent.com/fivepeople-art/terminal-setting-kit/main/install.sh | sh
   ```

3. 안내를 따라갑니다. 직접 하는 것은 넷입니다.
   - **Enter와 Mac 비밀번호**: 처음 앱 설치 도구(Homebrew)를 깔 때 'Press RETURN/ENTER to continue'가 나오면 Enter를 누르고, 비밀번호를 물으면 입력합니다(입력해도 화면에 글자가 안 보이는 게 정상).
   - **질문 하나**: "지금 한/A 키로 한영을 바꾸세요?" 예라고 하면 한/A를 짧게 누를 때 한영이 바뀌고, 누른 채 다른 키를 누를 때 Hyper 키가 됩니다.
   - **Karabiner 권한**: Karabiner-Elements 창이 열리면 창의 안내를 위에서부터 하나씩 따라 허용합니다(백그라운드 서비스, 손쉬운 사용, 입력 모니터링, 드라이버 확장 프로그램). 창의 버튼이 맞는 시스템 설정 화면을 엽니다. 마지막에 키보드 종류를 물으면 쓰는 키보드와 같은 것을 고릅니다(Apple 한국어 키보드는 보통 ANSI).
   - **Claude 로그인**: 처음 `claude`를 실행하면 브라우저에서 로그인합니다(Claude Pro 이상 계정).

중간에 이런 창이 뜰 수 있습니다. 모두 정상입니다.
- "명령어 라인 개발자 도구를 설치하겠습니까?": **설치**를 누릅니다(앱 설치 도구에 필요합니다).
- "인터넷에서 다운로드한 앱입니다. 여시겠습니까?"(Ghostty·Karabiner 처음 열 때): **열기**를 누릅니다.
- "백그라운드 항목이 추가됨"(Karabiner): 그대로 둡니다.
- "'Ghostty'을(를) 제어하려고 합니다"(처음 설정을 바꿀 때): **허용**을 누릅니다. 바뀐 설정을 Ghostty가 바로 다시 읽게 합니다(거절해도 Cmd+Shift+,로 다시 읽힘).

중간에 끊기면 같은 명령을 다시 붙여 넣으면 이어서 합니다.

**대문자 고정**은 Shift+한/A로 합니다(한/A가 Hyper 키가 되기 때문).

설치가 끝나면 '이제 해 볼 것'이 키 확인 순서를 보여 줍니다. 다시 보려면 `terminal-setting guide`.

## 설치되는 것

- 앱: Ghostty, Herdr, Karabiner-Elements, Claude Code, Geist Mono 글꼴, yazi(파일 탐색기)
- 단축키 40여 개, Herdr plugin 셋(닫기 전 확인, pane 크기 맞추기, 탭 이름 자동), 테마 셋(Eyes Day·fapibrown·Eyes Night)
- `terminal-setting` 명령과 Claude용 `terminal-setting` 스킬
- Claude 설정(쓰던 값이 없을 때만): 명령·파일 작업을 묻지 않고 바로 실행, Claude가 답을 기다리면 Ghostty 알림, 답변 방식 i-have-adhd(결론 먼저·번호 단계·쉬운 말). 끄기: `terminal-setting set claude-auto-approve off`, `terminal-setting set reply-style default`

전에 쓰던 터미널 설정은 설치 전에 `~/.local/state/terminal-setting/backups/`에 보관됩니다.

## 쓰기와 꾸미기

가장 쉬운 방법은 Claude에게 말하는 것입니다: "글자 좀 크게 해줘", "사이드바 넓게", "테마 바꾸는 단축키를 Hyper+Y로". 직접 고르고 싶으면 `terminal-setting customize`(번호 메뉴).

| 하고 싶은 것 | 명령 |
|---|---|
| 바꿀 수 있는 것과 지금 값 | `terminal-setting settings` |
| 하나 바꾸기 | `terminal-setting set font-size 18`, `terminal-setting set sidebar-width 24`, `terminal-setting set opacity 0.9` |
| 되돌리기 | `terminal-setting unset font-size`, 전부는 `terminal-setting reset` |
| 단축키 | `terminal-setting keys`(표), `terminal-setting key theme_toggle hyper+y`, 끄기 `… off`, 되돌리기 `… default` |
| Hyper 키·한영 | `terminal-setting set hyper-key right_option`, `terminal-setting set hangul-tap off` |
| Claude가 실행 전에 묻게 / 답변 방식 기본으로 | `terminal-setting set claude-auto-approve off` / `terminal-setting set reply-style default` |
| 테마 | Hyper+T, 또는 `terminal-setting theme list` |
| 점검 · 이 Mac 정보 · 새 판 · 지우기 | `terminal-setting doctor` · `terminal-setting env` · `terminal-setting update` · `terminal-setting uninstall` |

바꾼 것은 모두 `~/.config/terminal-setting/settings.toml` 한 파일에 남고, 업데이트해도 그대로입니다. 설정 파일을 직접 고쳐도 다음 업데이트 때 이 파일로 옮겨 지켜 줍니다.

## 라이선스

MIT([LICENSE](LICENSE)): 누구나 쓰고 고치고 나눌 수 있습니다. 안에 든 `plugins/confirm-close`는 원저자 Ajdien Taravati의 MIT 라이선스를 따릅니다(그 폴더의 LICENSE).

## 만든 곳

[FAPI](https://fapi.page)가 자기 Mac에서 쓰는 환경을 그대로 나눕니다. 이 레포는 원본에서 자동으로 만들어지므로 고칠 점은 이슈로 알려 주세요.

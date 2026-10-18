# Windows Widget

[English](README.md) · **한국어**

[Ubuntu Widget](https://github.com/KweonTJ/Ubuntu_Widget)의 Windows 11용 독립 버전입니다. 보관함에서 위젯을 골라 바탕화면에 놓고, 16px 그리드에 맞춰 이동·크기 조절·스택을 사용할 수 있습니다. 시스템 다크/라이트 모드와 선택형 Acrylic 글래스 효과를 지원합니다.

![위젯 보관함](docs/images/windows-library.png)

Microsoft·Apple의 공식 앱이 아닙니다. **Windows 첫 구현으로, 하드웨어 연동의 Windows 11 실기기 검증은 아직 필요합니다.** Ubuntu용 Eww·GTK는 사용하지 않습니다.

## 설치

- 지원 대상: **Windows 11 x64, 빌드 22000 이상**. Windows 10은 지원하지 않습니다. Acrylic은 OS 버전과 Windows 투명 효과 설정에 영향을 받습니다.
- [GitHub 릴리즈](https://github.com/KweonTJ/Ubuntu_Widget/releases/tag/windows-v1.0.0)에서 [설치 EXE](https://github.com/KweonTJ/Ubuntu_Widget/releases/download/windows-v1.0.0/windows-widget-1.0.0-x64-win.exe)를 내려받아 실행하세요. 사용자별 설치, 경로 선택, 시작 메뉴·바탕화면 바로가기와 제거 기능을 제공합니다. 관리자 권한, Python, Node.js, Eww는 필요하지 않습니다.
- 무설치 사용: `windows-widget-1.0.0-x64-win.zip` 전체를 풀고 **Widget Library.exe**를 실행하세요. 함께 들어 있는 런타임 파일을 유지해야 합니다.
- 보관함에서 위젯 선택 → **바탕화면에 추가**. 보관함의 작업 표시줄 아이콘은 Windows 메뉴에서 고정할 수 있습니다.
- 보관함을 닫아도 트레이에서 실행됩니다. 완전히 끝내려면 트레이 → **종료**. 자동 시작은 **설정 → 로그인 시 시작**에서 직접 켭니다.

처음 실행하면 빈 바탕화면으로 시작합니다. 현재 설치 파일에는 코드 서명이 없어 Windows에 알 수 없는 게시자로 표시될 수 있습니다. 자동 업데이트 서비스는 없으며 새 버전 설치 파일로 업데이트합니다. 사용자 데이터는 유지됩니다.

## 조작

| 기능 | 방법 |
| --- | --- |
| 이동 | 위젯 몸체를 드래그. 버튼·할 일 체크·노트 텍스트 선택은 해당 동작을 유지합니다. |
| 크기 | 좌우 가장자리로 너비, 하단 전체로 높이를 조절합니다. 모서리 조절도 가능합니다. |
| 스택 | 너비·높이가 같은 위젯을 65% 이상 겹쳐 놓습니다. 스택끼리도 합칠 수 있습니다. |
| 넘기기 | Precision Touchpad의 두 손가락 가로 스크롤, Shift+휠, 상단 페이지 번호. 세로 스크롤은 내용을 스크롤합니다. |
| 삭제·분리·크기 프리셋 | 위젯 오른쪽 클릭 또는 **내 바탕화면**. 눈에 보이는 X·이동 손잡이는 없습니다. |
| 테마·글래스 | **설정**에서 시스템/라이트/다크와 글래스 효과를 바꿉니다. |

프리셋 208×208 / 320×224 / 432×352, 최소 192×96 논리 픽셀입니다. 위치·크기는 16px 단위로 맞춥니다. 작업 표시줄을 피하고, 모니터가 바뀌면 화면 안으로 보정합니다. 스택은 하나의 창에서 내용을 전환하므로 페이지를 넘겨도 위치·크기가 바뀌지 않습니다. 작은 위젯의 넘치는 내용은 스크롤합니다.

위젯은 작업 표시줄에서 숨겨진 일반 Windows 창입니다. 항상 위에 고정하지 않으며 Explorer에 삽입하거나 Windows 기본 위젯 보드를 바꾸지 않습니다. **Win+D로 숨겨질 수 있으며**, 트레이 → **모든 위젯 표시**로 복원합니다. 보관함은 일반 작업 표시줄 아이콘을 제공합니다.

## 위젯과 사용자 설정

| 분류 | 제공 항목 |
| --- | --- |
| 시간·날짜 | 디지털/아날로그 시계, 일요일 시작 달력, 오늘, 세계 시계, 하루·올해 진행률, 디데이, 로컬 일정 |
| 시스템 | CPU, 메모리, 시스템 디스크, 네트워크, 가동 시간, 시스템 요약, PC·Bluetooth 배터리, 사용 시간, KDE Connect |
| 메모·집중 | Obsidian 노트, todomate 오늘 할 일, 집중 타이머·완료 알림 |
| 미디어·홈 | Windows 음악/팟캐스트·앨범 커버·재생 제어, 사운드 설정, 날씨, Home Assistant |
| 웹 | 토스증권 바로가기, Notion, 네이버 메일, Gmail, Google 캘린더, Keep, YouTube, Spotify, GitHub, 사용자 웹사이트 |

사용자 웹사이트 양식을 포함해 보관함에 **36개 항목**이 있습니다. 웹 위젯은 기본 브라우저로 여는 바로가기입니다. 가짜 실시간 데이터나 미리 연결된 계정은 없습니다.

- **날씨:** 설정에서 도시 검색 → 검색 결과 선택 → 추가/저장. 위도·경도 직접 입력도 가능합니다. Open-Meteo를 사용하고 10분 간격으로 갱신합니다. IP 기반 위치 추적은 없습니다. [데이터: Open-Meteo / CC BY 4.0](https://open-meteo.com/en/terms).
- **배터리:** PC 배터리와 연결 상태·잔량이 Windows에 노출되는 Bluetooth 기기만 표시합니다. 기기·드라이버에 따라 일부는 표시되지 않습니다. 배터리가 없는 데스크톱에는 PC 배터리가 나타나지 않습니다.
- **음악·팟캐스트:** Windows 미디어 세션을 제공하는 플레이어에서 재생하세요. 해당 앱이 제공하는 제목·커버·재생 제어를 사용하며, 외부 커버 검색은 하지 않습니다. 약 15~20초 간격으로 조회합니다. Windows 기본 PowerShell로 동봉된 고정 스크립트를 실행합니다.
- **todomate:** **todomate 로그인 / 열기** → 공식 사이트에서 직접 로그인. 오늘의 내 할 일만 표시·완료/취소합니다. 완료 항목은 아래의 접힌 영역으로 이동합니다. 비밀번호·토큰은 위젯 브리지로 전달하지 않습니다. 공식 페이지의 Firebase 클라이언트를 사용하는 **비공식 호환 연결**이므로 서비스 구조 변경에 영향을 받습니다. 이메일·비밀번호 로그인을 우선 대상으로 하며 외부 계정 로그인은 제공자가 차단할 수 있습니다. **연결 해제**는 로컬 로그인 저장소를 지웁니다.
- **Obsidian:** 보관함 안의 Markdown 파일 선택. 읽기 전용 텍스트로 표시하고 변경을 반영합니다. 편집은 Obsidian에서 진행하세요. 1MB 초과 파일은 읽지 않습니다. **Obsidian에서 열기**에는 설치된 Obsidian URI 연결이 필요합니다.
- **KDE Connect:** Windows용 앱을 기본 Program Files 경로에 설치 → 기기 페어링·파일 공유 켜기 → **파일 보내기…** → 기기 선택 → 파일 선택. 파일 선택을 마치면 전송합니다. 기기는 ID로 표시하며 전송·수신은 KDE Connect가 담당합니다.
- **Home Assistant:** 본인 서버 주소, 쉼표로 구분한 기기 ID, 장기 액세스 토큰 입력. 토큰은 Windows 사용자 자격 증명으로 암호화해 별도 저장합니다. 지정한 light/switch만 토글하고 다른 상태는 읽기 전용입니다. HTTPS 인증서를 검증합니다.
- **스크린 타임:** 설정에서 사용 시간 기록을 켜세요. 앱 실행 중이고 PC 유휴 시간이 60초 미만일 때 활성 프로그램 이름과 시간을 로컬에 기록합니다. 창 제목·웹 주소는 수집하지 않습니다. 과거 Windows 전체 기록과는 다릅니다. 끄면 새 기록을 멈추며, 종료 후 `layout.json`을 지우면 기록을 제거합니다.
- **토스증권:** 이 Windows 버전은 **바로가기만 제공**합니다. Ubuntu 시세 API를 Windows에서 검증하지 않았으며 API 키 수집·주문 기능은 없습니다.
- **일정·디데이·집중:** 사용자 PC에만 저장하며 캘린더 계정 동기화는 없습니다. 집중 타이머는 앱 종료 시 초기화합니다.

아이폰 연속성, 자동 Bluetooth 페어링, 계정 자동 이전, 직접 볼륨 슬라이더, Apple 서비스 연동은 제공하지 않습니다.

## 데이터·개인정보

저장 위치는 `%APPDATA%\windows-widget\`입니다. `layout.json`에 배치·설정·선택 파일 경로·사용 시간, `credentials.json`에 암호화한 Home Assistant 토큰, `Partitions\todomate`에 격리된 웹 로그인을 저장합니다. Windows 계정마다 분리됩니다. 제거 프로그램은 데이터를 보존하며, 완전히 초기화하려면 앱 종료 후 해당 폴더를 직접 삭제하세요.

배포물에 개발자의 Ubuntu 개인정보는 포함하지 않습니다. 사용 통계 전송은 없습니다. 날씨·todomate·Home Assistant는 사용자가 해당 연결을 설정한 뒤 통신합니다. 웹사이트 자체의 추적 정책은 각 서비스에 따릅니다.

## 수정·빌드

Windows 11에서 Node.js 22 이상을 설치하세요.

```powershell
npm ci
npm test
npm start
npm run build
```

`dist/`에 x64 설치 EXE와 무설치 ZIP을 만듭니다. ARM64는 `npm run build:arm64`로 시험 빌드할 수 있지만 ARM 기기에서 검증되지 않았습니다. 의존성은 lockfile로 고정합니다.

저장소 루트의 [Windows 워크플로](../.github/workflows/windows.yml)는 `windows-widget/`에서 테스트·PowerShell 어댑터 확인·격리 UI 검증·패키징·SHA-256 생성을 수행하고 산출물을 보관합니다. `windows-v*` 태그로 Ubuntu와 버전을 구분하며, 검증한 산출물은 GitHub Releases로 게시합니다. 태그 버전은 이 폴더의 package.json과 맞추세요.

동봉한 NSIS 스크립트로 Linux에서도 설치 파일을 빌드할 수 있지만 **Windows 11 실기기 실행 검증과 같지 않습니다.** 검증 범위는 [VALIDATION.md](docs/VALIDATION.md)를 확인하세요.

수정 위치: `src/catalog.cjs`(목록), `renderer/app.js`(위젯 내용), `renderer/style.css`(디자인), `src/model.cjs`(배치·스택), `src/providers.cjs`·`native/windows.ps1`(데이터), `src/main.cjs`(창·IPC).

## 릴리즈

버전별 패키지·상세 변경 내용은 GitHub Releases로 관리합니다. 영문·한글 README에는 버전별 요약 한 줄씩만 추가하고, 이전 버전 파일을 덮어쓰지 않습니다.

| 버전 | 주요 내용 |
| --- | --- |
| [Windows v1.0.0](https://github.com/KweonTJ/Ubuntu_Widget/releases/tag/windows-v1.0.0) — 프리릴리즈 | Windows 11 보관함, 독립 위젯, 그리드 크기 조절, 스택, 테마·Windows 데이터 어댑터. |

MIT. [사용한 오픈소스](THIRD_PARTY_NOTICES.md).

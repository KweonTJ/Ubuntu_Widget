"""Built-in library metadata; no network access needed to browse it."""
CATEGORIES = [('all','전체 위젯'),('added','내 바탕화면'),('time','시간과 날짜'),
              ('productivity','메모와 집중'),('system','시스템'),('media','음악과 사운드'),('life','날씨와 홈'),('finance','주식'),('web','웹사이트')]
EXTRAS = [
 ('weather','날씨','life','직접 선택한 도시의 현재 기온·최고/최저·시간대별·7일 예보와 대기질을 확인합니다.'),
 ('analog','아날로그 시계','time','이 PC의 현지 시각을 아날로그 시계로 표시합니다. 1분마다 바늘이 움직입니다.'),
 ('agenda','다가오는 일정','time','날짜와 시간을 입력한 약속을 가까운 순서대로 봅니다. 이 PC에 저장하는 일정입니다.'),
 ('stocks','주식 · 토스증권','finance','본인의 토스증권 Open API를 직접 연결합니다. 관심 종목과 시장 지수를 30초마다 조회합니다.'),
 ('screentime','스크린 타임','system','기록을 켠 뒤부터 오늘의 앱별 사용 시간을 확인합니다. 기록은 이 PC에만 저장됩니다.'),
 ('home','홈','life','개인의 Home Assistant 서버를 연결해 기기 상태를 보고 조명·스위치를 제어합니다.'),
 ('podcast','팟캐스트','media','MPRIS를 지원하는 플레이어나 브라우저에서 재생한 팟캐스트를 확인하고 제어합니다.'),
 ('worldclock','세계 시계','time','서울·도쿄·런던·뉴욕의 현지 시각을 함께 봅니다. 서머타임을 반영합니다.'),
 ('today','오늘 날짜','time','오늘의 날짜, 요일과 올해의 몇 번째 주인지 크게 표시합니다.'),
 ('dayprogress','하루 진행률','time','오늘이 얼마나 지났는지와 자정까지 남은 시간을 확인합니다.'),
 ('yearprogress','올해 진행률','time','올해의 진행률과 다음 해까지 남은 일수를 확인합니다.'),
 ('countdown','디데이','time','기억하고 싶은 날짜와 제목을 설정하고 남은 날짜를 확인합니다.'),
 ('note','Obsidian 노트','productivity','보관함의 Markdown 노트를 선택해 실시간으로 읽고 Obsidian에서 엽니다.'),
 ('todo','todomate 할 일','productivity','todomate의 오늘 할 일을 표시하고 완료를 체크합니다. 계정은 이 PC에서 직접 연결하세요.'),
 ('focus','집중 타이머','productivity','집중 시간을 정하고 시작·일시정지·초기화합니다. 완료하면 알림을 보냅니다.'),
 ('cpu','CPU 사용량','system','프로세서 사용률을 실시간으로 표시합니다.'),
 ('memory','메모리','system','현재 메모리 사용률과 사용 중인 용량을 확인합니다.'),
 ('disk','저장공간','system','홈 폴더가 있는 디스크의 사용률과 남은 공간을 확인합니다.'),
 ('network','네트워크 속도','system','루프백을 제외한 네트워크 인터페이스의 합산 다운로드·업로드 속도입니다.'),
 ('uptime','PC 가동 시간','system','이번 부팅 이후 PC가 켜져 있던 시간을 확인합니다.'),
 ('kdeconnect','KDE Connect · 파일 공유','system','연결된 기기를 확인하고 여러 파일을 한 번에 보냅니다. KDE Connect에서 기기 연결과 파일 공유를 먼저 켜 주세요.'),
]
EXTRA_WIDGETS = [dict(id='uw-'+kind,name=name,kind=kind,category=category,
                      description=desc,icon='applications-utilities-symbolic',
                      configurable=kind in ('note','todo','focus','countdown','agenda','stocks','weather','home','screentime'))
                 for kind,name,category,desc in EXTRAS]
SITE_PRESETS = [dict(id='preset-'+key,name=name,kind='webpreset',category='web',url=url,
                    description='바탕화면 바로가기로 추가합니다. 누르면 독립 웹앱 창에서 열립니다.',
                    icon='web-browser-symbolic') for key,name,url in [
    ('notion','노션','https://www.notion.so/'),
    ('naver-mail','네이버 메일','https://mail.naver.com/'),
    ('gmail','Gmail','https://mail.google.com/'),
    ('calendar','Google 캘린더','https://calendar.google.com/'),
    ('keep','Google Keep','https://keep.google.com/'),
    ('youtube','YouTube','https://www.youtube.com/'),
    ('spotify','Spotify','https://open.spotify.com/'),
    ('github','GitHub','https://github.com/')]]
ORIGINAL_CATEGORIES = {'clock':'time','calendar':'time','system':'system','battery':'system',
                       'music':'media','sound':'media'}

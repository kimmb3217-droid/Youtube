# FFMPEG 설치 및 연동 가이드 (Windows)

YouTube의 고화질(1080p, 1440p, 4K 등) 영상은 비디오와 오디오가 분리되어 다운로드되므로, 두 파일을 하나로 합쳐줄 `ffmpeg`가 반드시 필요합니다.

프로그램이 `ffmpeg`를 올바르게 인식하도록 설정하는 방법은 두 가지가 있습니다. 편한 방법을 선택해 주세요.

---

## 방법 1: 프로젝트 폴더에 직접 넣기 (가장 쉽고 권장됨)

1. [ffmpeg 공식 빌드 페이지 (gyan.dev)](https://www.gyan.dev/ffmpeg/builds/) 또는 직접 다운로드 링크에서 `ffmpeg-git-full.7z` (또는 zip) 파일을 다운로드합니다.
   - 우회/빠른 다운로드 링크: [ffmpeg-release-essentials.zip](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip)
2. 다운로드한 압축 파일의 압축을 풉니다.
3. 압축을 풀면 나오는 `bin` 폴더 안의 파일들 중 **`ffmpeg.exe`**와 **`ffprobe.exe`**를 복사합니다.
4. 이 프로젝트 폴더(`d:\youtube`) 안에 **`bin`**이라는 이름의 폴더를 생성하고, 그 안에 복사한 파일들을 붙여넣습니다.
   - 최종 구조:
     ```text
     d:\youtube\
     ├── bin\
     │   ├── ffmpeg.exe
     │   └── ffprobe.exe
     ├── downloader.py
     ├── gui.py
     └── main.py
     ```

---

## 방법 2: Windows 시스템 환경 변수(PATH)에 등록하기

이미 시스템에 `ffmpeg`가 설치되어 있고 환경 변수(`PATH`)에 등록되어 있다면, 프로그램이 자동으로 인식하므로 추가 작업이 필요 없습니다.

만약 새로 등록하려면:
1. `ffmpeg.exe`가 있는 폴더의 절대 경로를 복사합니다 (예: `C:\ffmpeg\bin`).
2. Windows 검색창에 `시스템 환경 변수 편집`을 검색하여 실행합니다.
3. `환경 변수(N)...` 버튼을 클릭합니다.
4. `시스템 변수` 목록에서 `Path`를 찾아 선택한 뒤 `편집(I)...`을 누릅니다.
5. `새로 만들기(N)`를 누르고 복사한 경로를 입력한 후 `확인`을 누릅니다.
6. 모든 창의 `확인`을 눌러 저장한 후, 터미널이나 프로그램을 다시 시작합니다.

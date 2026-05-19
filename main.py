import os
from gui import YoutubeDownloaderApp

def main():
    # 필수 폴더 자동 생성 (bin: ffmpeg 배치용, downloads: 기본 다운로드 위치)
    os.makedirs(os.path.join(os.getcwd(), "bin"), exist_ok=True)
    os.makedirs(os.path.join(os.getcwd(), "downloads"), exist_ok=True)

    # GUI 프로그램 구동
    app = YoutubeDownloaderApp()
    app.mainloop()

if __name__ == "__main__":
    main()

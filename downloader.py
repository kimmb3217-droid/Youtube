import os
import shutil
import subprocess
import yt_dlp

class YoutubeDownloader:
    def __init__(self, ffmpeg_dir=None):
        self.ffmpeg_dir = ffmpeg_dir
        self.ffmpeg_path = self._resolve_ffmpeg_path()

    def _resolve_ffmpeg_path(self):
        """
        ffmpeg.exe의 위치를 탐색합니다.
        1. 지정된 ffmpeg_dir
        2. 현재 작업 디렉토리 아래의 bin/ffmpeg.exe
        3. 시스템 PATH
        """
        # 1. 지정된 디렉토리 확인
        if self.ffmpeg_dir:
            path = os.path.join(self.ffmpeg_dir, "ffmpeg.exe")
            if os.path.exists(path):
                return path

        # 2. 현재 작업 디렉토리의 bin/ffmpeg.exe 확인
        local_bin_path = os.path.join(os.getcwd(), "bin", "ffmpeg.exe")
        if os.path.exists(local_bin_path):
            return local_bin_path

        # 3. 시스템 PATH에서 ffmpeg 탐색
        system_path = shutil.which("ffmpeg")
        if system_path:
            return system_path

        return None

    def is_ffmpeg_available(self):
        """
        ffmpeg이 시스템이나 로컬 디렉토리에서 사용 가능한지 확인합니다.
        """
        if self.ffmpeg_path:
            try:
                # 실행 테스트
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                subprocess.run(
                    [self.ffmpeg_path, "-version"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    startupinfo=startupinfo,
                    check=True
                )
                return True
            except Exception:
                return False
        return False

    def get_video_info(self, url):
        """
        유튜브 동영상의 기본 정보 및 다운로드 가능한 해상도 목록을 추출합니다.
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
        }
        if self.ffmpeg_path:
            ydl_opts['ffmpeg_location'] = self.ffmpeg_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                
                # 플레이리스트인지 단일 영상인지 판단
                is_playlist = 'entries' in info
                
                if is_playlist:
                    # 플레이리스트의 경우 첫 번째 비디오 혹은 요약 정보 활용
                    entries = list(info.get('entries', []))
                    if not entries:
                        raise Exception("플레이리스트가 비어 있습니다.")
                    
                    return {
                        'success': True,
                        'title': info.get('title', 'Unknown Playlist'),
                        'uploader': info.get('uploader', 'Unknown Uploader'),
                        'duration': f"영상 {len(entries)}개",
                        'thumbnail': entries[0].get('thumbnail', '') if entries[0] else '',
                        'heights': ["최고 화질"],
                        'is_playlist': True,
                        'raw_info': info
                    }
                
                # 단일 영상인 경우 해상도 목록 추출
                formats = info.get('formats', [])
                heights = set()
                for f in formats:
                    h = f.get('height')
                    # 비디오 코덱이 존재하고(오디오 전용이 아님) 높이가 유효한 경우만
                    if h and f.get('vcodec') != 'none':
                        heights.add(h)
                
                sorted_heights = sorted(list(heights), reverse=True)
                heights_list = [f"{h}p" for h in sorted_heights]
                
                # 항상 최고 화질 옵션을 맨 앞에 추가
                if "최고 화질" not in heights_list:
                    heights_list.insert(0, "최고 화질")
                
                # 재생 시간 포맷팅
                duration = info.get('duration')
                duration_str = "00:00"
                if duration:
                    m, s = divmod(duration, 60)
                    h, m = divmod(m, 60)
                    duration_str = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
                
                return {
                    'success': True,
                    'title': info.get('title', 'Unknown Title'),
                    'uploader': info.get('uploader', 'Unknown Uploader'),
                    'duration': duration_str,
                    'thumbnail': info.get('thumbnail', ''),
                    'heights': heights_list,
                    'is_playlist': False,
                    'raw_info': info
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }

    def download_video(self, url, quality="최고 화질", output_dir="downloads", audio_only=False, progress_callback=None):
        """
        동영상을 다운로드합니다.
        quality: "최고 화질", "2160p", "1440p", "1080p", "720p", "480p", "360p" 등
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        ydl_opts = {
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
        }

        # ffmpeg 경로 연동
        if self.ffmpeg_path:
            ydl_opts['ffmpeg_location'] = self.ffmpeg_path
        
        # 포맷 설정
        if audio_only:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            if quality == "최고 화질" or not quality:
                # 최고 비디오와 최고 오디오 결합
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
            else:
                # 특정 화질 이하 중 최고 화질 선택
                height = quality.replace("p", "")
                ydl_opts['format'] = f'bestvideo[height<={height}]+bestaudio/best/best[height<={height}]'
            
            # 고화질 스트림 결합 시 기본 MP4 포맷으로 저장 유도
            ydl_opts['merge_output_format'] = 'mp4'

        def hook(d):
            if progress_callback:
                status = d.get('status')
                if status == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    downloaded = d.get('downloaded_bytes', 0)
                    speed = d.get('speed') or 0 # bytes/sec
                    eta = d.get('eta') or 0 # seconds
                    filename = os.path.basename(d.get('filename', ''))
                    
                    percent = (downloaded / total) * 100 if total > 0 else 0
                    progress_callback({
                        'status': 'downloading',
                        'percent': percent,
                        'downloaded': downloaded,
                        'total': total,
                        'speed': speed,
                        'eta': eta,
                        'filename': filename
                    })
                elif status == 'finished':
                    progress_callback({
                        'status': 'merging',
                        'percent': 100.0,
                        'filename': os.path.basename(d.get('filename', ''))
                    })

        ydl_opts['progress_hooks'] = [hook]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            if progress_callback:
                progress_callback({'status': 'completed', 'percent': 100.0})
            return {'success': True}
        except Exception as e:
            if progress_callback:
                progress_callback({'status': 'error', 'error': str(e)})
            return {'success': False, 'error': str(e)}

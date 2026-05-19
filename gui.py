import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

# Pillow가 있으면 썸네일 로드 가능, 없으면 텍스트로 대체
try:
    from PIL import Image, ImageTk
    import io
    import urllib.request
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

from downloader import YoutubeDownloader

# 테마 설정
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue" 중 선택

class YoutubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube 고화질 다운로더")
        self.geometry("780x560")
        self.resizable(False, False)

        # 다운로더 인스턴스
        self.downloader = YoutubeDownloader()
        self.save_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # 상태 변수들
        self.analyzing = False
        self.downloading = False
        self.video_info = None

        # UI 초기 설정
        self.setup_ui()
        self.check_ffmpeg()

    def setup_ui(self):
        # 전체 레이아웃 그리드 구성
        self.grid_columnconfigure(0, weight=3) # 좌측: 정보 영역
        self.grid_columnconfigure(1, weight=4) # 우측: 설정/실행 영역
        self.grid_rowconfigure(0, weight=1)

        # ==========================================
        # 좌측 패널 (영상 정보 카드)
        # ==========================================
        self.left_panel = ctk.CTkFrame(self, corner_radius=15, fg_color="#1e1e24")
        self.left_panel.grid(row=0, column=0, padx=(15, 7), pady=15, sticky="nsew")
        
        # 썸네일 영역
        self.thumb_label = ctk.CTkLabel(
            self.left_panel, 
            text="동영상 분석 전\n(유튜브 URL을 분석해 주세요)", 
            width=280, 
            height=180, 
            fg_color="#2b2b36", 
            corner_radius=10
        )
        self.thumb_label.pack(padx=15, pady=20)

        # 정보 상세 영역
        self.info_title_label = ctk.CTkLabel(self.left_panel, text="제목:", font=ctk.CTkFont(weight="bold"))
        self.info_title_label.pack(anchor="w", padx=20, pady=(5, 0))
        self.info_title_val = ctk.CTkLabel(self.left_panel, text="-", font=ctk.CTkFont(size=12), justify="left", wraplength=260)
        self.info_title_val.pack(anchor="w", padx=20, pady=(0, 10))

        self.info_uploader_label = ctk.CTkLabel(self.left_panel, text="채널명:", font=ctk.CTkFont(weight="bold"))
        self.info_uploader_label.pack(anchor="w", padx=20, pady=(5, 0))
        self.info_uploader_val = ctk.CTkLabel(self.left_panel, text="-", font=ctk.CTkFont(size=12))
        self.info_uploader_val.pack(anchor="w", padx=20, pady=(0, 10))

        self.info_duration_label = ctk.CTkLabel(self.left_panel, text="재생 시간:", font=ctk.CTkFont(weight="bold"))
        self.info_duration_label.pack(anchor="w", padx=20, pady=(5, 0))
        self.info_duration_val = ctk.CTkLabel(self.left_panel, text="-", font=ctk.CTkFont(size=12))
        self.info_duration_val.pack(anchor="w", padx=20, pady=(0, 10))

        # ffmpeg 상태 표시
        self.ffmpeg_status_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.ffmpeg_status_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        self.ffmpeg_info_row = ctk.CTkFrame(self.ffmpeg_status_frame, fg_color="transparent")
        self.ffmpeg_info_row.pack(fill="x", anchor="w")
        
        self.ffmpeg_status_indicator = ctk.CTkLabel(
            self.ffmpeg_info_row, 
            text="●", 
            text_color="#ff5555", 
            font=ctk.CTkFont(size=14)
        )
        self.ffmpeg_status_indicator.pack(side="left", padx=(0, 5))
        
        self.ffmpeg_status_text = ctk.CTkLabel(
            self.ffmpeg_info_row, 
            text="ffmpeg 미연동 (고화질 다운로드 불가)", 
            font=ctk.CTkFont(size=11)
        )
        self.ffmpeg_status_text.pack(side="left")

        self.ffmpeg_install_btn = ctk.CTkButton(
            self.ffmpeg_status_frame,
            text="FFmpeg 자동 설치",
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#3a3a46",
            hover_color="#4f4f5f",
            command=self.start_ffmpeg_install_thread
        )

        # ==========================================
        # 우측 패널 (제어 카드)
        # ==========================================
        self.right_panel = ctk.CTkFrame(self, corner_radius=15, fg_color="#1e1e24")
        self.right_panel.grid(row=0, column=1, padx=(7, 15), pady=15, sticky="nsew")

        # 타이틀
        self.app_title = ctk.CTkLabel(
            self.right_panel, 
            text="YouTube Downloader", 
            font=ctk.CTkFont(size=24, weight="bold", family="Outfit")
        )
        self.app_title.pack(anchor="w", padx=20, pady=(20, 15))

        # 1. URL 입력 및 분석
        self.url_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.url_frame.pack(fill="x", padx=20, pady=5)
        
        self.url_entry = ctk.CTkEntry(
            self.url_frame, 
            placeholder_text="유튜브 동영상 링크를 붙여넣으세요 (Ctrl+V)", 
            height=35
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.analyze_btn = ctk.CTkButton(
            self.url_frame, 
            text="링크 분석", 
            width=80, 
            height=35, 
            command=self.start_analyze_thread
        )
        self.analyze_btn.pack(side="right")

        # 2. 저장 폴더 설정
        self.path_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.path_frame.pack(fill="x", padx=20, pady=15)
        
        self.path_btn = ctk.CTkButton(
            self.path_frame, 
            text="저장 경로...", 
            width=90, 
            height=30, 
            fg_color="#3a3a46", 
            hover_color="#4f4f5f",
            command=self.browse_folder
        )
        self.path_btn.pack(side="left", padx=(0, 10))
        
        self.path_label = ctk.CTkLabel(
            self.path_frame, 
            text=self.save_dir, 
            font=ctk.CTkFont(size=11), 
            anchor="w",
            wraplength=280
        )
        self.path_label.pack(side="left", fill="x", expand=True)

        # 구분선
        self.separator = ctk.CTkFrame(self.right_panel, height=2, fg_color="#2b2b36")
        self.separator.pack(fill="x", padx=20, pady=5)

        # 3. 옵션 선택
        self.option_title = ctk.CTkLabel(
            self.right_panel, 
            text="다운로드 설정", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.option_title.pack(anchor="w", padx=20, pady=(10, 5))

        # 다운로드 타입 (비디오 vs 오디오)
        self.type_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.type_frame.pack(fill="x", padx=20, pady=5)
        
        self.download_type = ctk.StringVar(value="video")
        self.type_video_radio = ctk.CTkRadioButton(
            self.type_frame, 
            text="비디오 다운로드 (MP4/MKV)", 
            variable=self.download_type, 
            value="video",
            command=self.toggle_download_type
        )
        self.type_video_radio.pack(side="left", padx=(0, 20))
        
        self.type_audio_radio = ctk.CTkRadioButton(
            self.type_frame, 
            text="오디오만 추출 (MP3)", 
            variable=self.download_type, 
            value="audio",
            command=self.toggle_download_type
        )
        self.type_audio_radio.pack(side="left")

        # 화질/해상도 선택 드롭다운
        self.resolution_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.resolution_frame.pack(fill="x", padx=20, pady=10)
        
        self.res_label = ctk.CTkLabel(self.resolution_frame, text="해상도 선택:")
        self.res_label.pack(side="left", padx=(0, 10))
        
        self.res_dropdown = ctk.CTkComboBox(
            self.resolution_frame, 
            values=["최고 화질"],
            state="disabled",
            width=150
        )
        self.res_dropdown.pack(side="left")

        # 4. 진행률 표시 영역
        self.progress_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=20, pady=(20, 5))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame, 
            text="대기 중...", 
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        self.progress_label.pack(fill="x")

        # 5. 다운로드 시작 버튼
        self.download_btn = ctk.CTkButton(
            self.right_panel, 
            text="다운로드 시작", 
            height=45, 
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#e50914", 
            hover_color="#b20710",
            state="disabled",
            command=self.start_download_thread
        )
        self.download_btn.pack(fill="x", padx=20, pady=(15, 20))

    # ==========================================
    # 기능 로직 함수
    # ==========================================
    def check_ffmpeg(self):
        """ffmpeg의 사용 가능 여부를 점검하고 표시합니다."""
        if self.downloader.is_ffmpeg_available():
            self.ffmpeg_status_indicator.configure(text_color="#39ff14")
            self.ffmpeg_status_text.configure(text="ffmpeg 연동됨 (고화질 병합 가능)")
            if hasattr(self, 'ffmpeg_install_btn'):
                self.ffmpeg_install_btn.pack_forget()
        else:
            self.ffmpeg_status_indicator.configure(text_color="#ff3333")
            self.ffmpeg_status_text.configure(text="ffmpeg 미연동 (최대 720p 제한 또는 실패 가능)")
            if hasattr(self, 'ffmpeg_install_btn'):
                self.ffmpeg_install_btn.pack(fill="x", pady=(5, 0))

    def browse_folder(self):
        """저장할 폴더를 브라우징하여 선택합니다."""
        folder = filedialog.askdirectory(initialdir=self.save_dir)
        if folder:
            self.save_dir = os.path.normpath(folder)
            self.path_label.configure(text=self.save_dir)

    def toggle_download_type(self):
        """비디오/오디오 다운로드 토글 시 드롭다운 상태를 바꿉니다."""
        if self.download_type.get() == "audio":
            self.res_dropdown.configure(state="disabled")
        else:
            # 동영상이 파싱되어 있을 때만 활성화
            if self.video_info:
                self.res_dropdown.configure(state="readonly")

    # ==========================================
    # 백그라운드 스레드: 동영상 정보 분석
    # ==========================================
    def start_analyze_thread(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("입력 오류", "유튜브 URL을 입력해 주세요.")
            return

        self.analyzing = True
        self.analyze_btn.configure(state="disabled", text="분석 중...")
        self.url_entry.configure(state="disabled")
        self.progress_label.configure(text="유튜브 서버에서 영상 정보를 가져오는 중...")
        
        # 스레드 구동
        t = threading.Thread(target=self._analyze_logic, args=(url,), daemon=True)
        t.start()

    def _analyze_logic(self, url):
        res = self.downloader.get_video_info(url)
        # 메인 스레드에 결과 반영
        self.after(0, lambda: self._apply_analyze_result(res))

    def _apply_analyze_result(self, res):
        self.analyzing = False
        self.analyze_btn.configure(state="normal", text="링크 분석")
        self.url_entry.configure(state="normal")

        if not res['success']:
            self.progress_label.configure(text="분석 실패.")
            messagebox.showerror("분석 실패", f"동영상 정보를 추출하지 못했습니다.\n\n오류 내용:\n{res.get('error')}")
            return

        self.video_info = res
        
        # UI 업데이트
        self.info_title_val.configure(text=res['title'])
        self.info_uploader_val.configure(text=res['uploader'])
        self.info_duration_val.configure(text=res['duration'])
        
        # 썸네일 가져오기
        if HAS_PILLOW and res['thumbnail']:
            # 스레드로 썸네일 이미지 불러오기
            threading.Thread(target=self._load_thumbnail, args=(res['thumbnail'],), daemon=True).start()
        else:
            self.thumb_label.configure(text="썸네일 로드 불가\n(Pillow 없음 또는 파일 없음)")

        # 해상도 메뉴 업데이트
        self.res_dropdown.configure(values=res['heights'])
        self.res_dropdown.set(res['heights'][0])

        if self.download_type.get() == "video":
            self.res_dropdown.configure(state="readonly")
        
        self.download_btn.configure(state="normal")
        self.progress_label.configure(text="정보 분석 완료! 다운로드 준비되었습니다.")

    def _load_thumbnail(self, url):
        try:
            # urllib를 이용한 간단한 이미지 파싱
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                image_data = response.read()
            
            img = Image.open(io.BytesIO(image_data))
            # 썸네일 비율 맞춰서 리사이즈 (280x180 이내)
            img.thumbnail((280, 180))
            
            # Tkinter 호환 이미지로 변환
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            
            # 메인 스레드에서 이미지 업데이트
            self.after(0, lambda: self._apply_thumbnail(ctk_img))
        except Exception as e:
            print(f"Thumbnail load error: {e}")
            self.after(0, lambda: self.thumb_label.configure(text="썸네일 로드 에러"))

    def _apply_thumbnail(self, ctk_img):
        self.thumb_label.configure(image=ctk_img, text="")

    # ==========================================
    # 백그라운드 스레드: 다운로드 실행
    # ==========================================
    def start_download_thread(self):
        if not self.video_info:
            return

        url = self.url_entry.get().strip()
        quality = self.res_dropdown.get()
        audio_only = (self.download_type.get() == "audio")

        # 다운로드 중 UI 고정
        self.set_ui_state_for_download(True)
        self.progress_bar.set(0)
        self.progress_label.configure(text="다운로드 시작 준비 중...")

        # ffmpeg가 설치되어 있지 않고 고화질 또는 오디오 추출을 시도할 때 경고
        if not self.downloader.is_ffmpeg_available():
            if audio_only or (quality != "360p" and quality != "480p" and quality != "720p"):
                warning_msg = (
                    "시스템에 ffmpeg가 확인되지 않았습니다!\n\n"
                    "ffmpeg가 없으면 1080p 이상의 고화질 병합이 동작하지 않거나, "
                    "오디오 파일(.mp3) 변환이 불가능할 수 있습니다.\n"
                    "다운로드를 강제 진행하시겠습니까?"
                )
                if not messagebox.askyesno("ffmpeg 경고", warning_msg):
                    self.set_ui_state_for_download(False)
                    self.progress_label.configure(text="다운로드 취소됨 (ffmpeg 없음)")
                    return

        # 스레드 구동
        t = threading.Thread(
            target=self._download_logic, 
            args=(url, quality, audio_only), 
            daemon=True
        )
        t.start()

    def set_ui_state_for_download(self, downloading):
        """다운로드 시작/완료 시 컴포넌트 활성화/비활성화"""
        self.downloading = downloading
        state = "disabled" if downloading else "normal"
        
        self.analyze_btn.configure(state=state)
        self.url_entry.configure(state=state)
        self.path_btn.configure(state=state)
        self.type_video_radio.configure(state=state)
        self.type_audio_radio.configure(state=state)
        
        if downloading:
            self.res_dropdown.configure(state="disabled")
            self.download_btn.configure(state="disabled", text="다운로드 중...")
        else:
            if self.download_type.get() == "video":
                self.res_dropdown.configure(state="readonly")
            self.download_btn.configure(state="normal", text="다운로드 시작")

    def _download_logic(self, url, quality, audio_only):
        def progress_callback(data):
            # 메인 스레드에 진행 보고 전달
            self.after(0, lambda: self._update_progress_ui(data))

        res = self.downloader.download_video(
            url=url,
            quality=quality,
            output_dir=self.save_dir,
            audio_only=audio_only,
            progress_callback=progress_callback
        )
        
        self.after(0, lambda: self._download_finished(res))

    def _update_progress_ui(self, data):
        status = data.get('status')
        if status == 'downloading':
            percent = data.get('percent', 0.0)
            self.progress_bar.set(percent / 100.0)
            
            # 속도 포맷팅
            speed = data.get('speed', 0)
            if speed > 1024 * 1024:
                speed_str = f"{speed / (1024 * 1024):.2f} MB/s"
            elif speed > 1024:
                speed_str = f"{speed / 1024:.2f} KB/s"
            else:
                speed_str = f"{speed:.2f} B/s"

            # ETA 포맷팅
            eta = data.get('eta', 0)
            eta_str = f"{eta}초" if eta else "계산 중"

            self.progress_label.configure(
                text=f"다운로드 중... [진행률: {percent:.1f}% | 속도: {speed_str} | 남은시간: {eta_str}]"
            )
        elif status == 'merging':
            self.progress_bar.set(0.95)
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self.progress_label.configure(text="다운로드 완료! ffmpeg를 사용해 영상/소리 병합 중...")
        elif status == 'completed':
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(1.0)
            self.progress_label.configure(text="성공적으로 다운로드 완료되었습니다!")
        elif status == 'error':
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_label.configure(text="다운로드 에러 발생.")

    def _download_finished(self, res):
        self.set_ui_state_for_download(False)
        
        if res['success']:
            messagebox.showinfo("다운로드 완료", f"성공적으로 다운로드 되었습니다!\n저장 경로:\n{self.save_dir}")
            # 완료 시 폴더 열기 유도
            if os.path.exists(self.save_dir):
                try:
                    os.startfile(self.save_dir)
                except Exception:
                    pass
        else:
            # 오류 메시지 세부 분석
            err_msg = res.get('error', '알 수 없는 오류')
            messagebox.showerror("다운로드 실패", f"다운로드 도중 에러가 발생했습니다.\n\n오류 설명:\n{err_msg}")

    # ==========================================
    # 백그라운드 스레드: FFmpeg 자동 설치
    # ==========================================
    def start_ffmpeg_install_thread(self):
        self.ffmpeg_install_btn.configure(state="disabled", text="설치 준비 중...")
        self.ffmpeg_status_text.configure(text="ffmpeg 다운로드 준비 중...")
        
        t = threading.Thread(target=self._ffmpeg_install_logic, daemon=True)
        t.start()

    def _ffmpeg_install_logic(self):
        import urllib.request
        import zipfile
        import shutil
        import ssl

        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        zip_path = os.path.join(os.getcwd(), "ffmpeg_temp.zip")
        extract_path = os.path.join(os.getcwd(), "ffmpeg_temp_extracted")
        bin_dir = os.path.join(os.getcwd(), "bin")

        try:
            # 1. Download
            self.after(0, lambda: self.ffmpeg_status_text.configure(text="ffmpeg 다운로드 중 (약 35MB)..."))
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            context = ssl._create_unverified_context()
            
            with urllib.request.urlopen(req, context=context) as response, open(zip_path, 'wb') as out_file:
                total_size = int(response.getheader('Content-Length') or 0)
                if total_size > 0:
                    downloaded = 0
                    block_size = 1024 * 512 # 512KB chunks
                    while True:
                        block = response.read(block_size)
                        if not block:
                            break
                        out_file.write(block)
                        downloaded += len(block)
                        percent = (downloaded / total_size) * 100
                        # Update status text in main thread
                        self.after(0, lambda p=percent: self.ffmpeg_status_text.configure(
                            text=f"ffmpeg 다운로드 중... ({p:.1f}%)"
                        ))
                else:
                    shutil.copyfileobj(response, out_file)

            # 2. Extract
            self.after(0, lambda: self.ffmpeg_status_text.configure(text="압축 해제 중..."))
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            # 3. Copy binaries
            self.after(0, lambda: self.ffmpeg_status_text.configure(text="실행 파일 복사 중..."))
            os.makedirs(bin_dir, exist_ok=True)
            copied = []
            for root, dirs, files in os.walk(extract_path):
                for file in files:
                    if file in ("ffmpeg.exe", "ffprobe.exe"):
                        src = os.path.join(root, file)
                        dst = os.path.join(bin_dir, file)
                        shutil.copy2(src, dst)
                        copied.append(file)

            # 4. Clean up
            self.after(0, lambda: self.ffmpeg_status_text.configure(text="임시 파일 정리 중..."))
            if os.path.exists(zip_path):
                try: os.remove(zip_path)
                except: pass
            if os.path.exists(extract_path):
                try: shutil.rmtree(extract_path)
                except: pass

            # 5. Complete
            if len(copied) >= 2:
                success = self.downloader.re_resolve_ffmpeg()
                if success:
                    self.after(0, lambda: self._ffmpeg_install_finished(True, "설치 완료!"))
                else:
                    self.after(0, lambda: self._ffmpeg_install_finished(False, "연동 확인 실패 (다시 시도해 주세요)"))
            else:
                self.after(0, lambda: self._ffmpeg_install_finished(False, "필수 파일 복사 누락"))

        except Exception as e:
            # Clean up on error
            if os.path.exists(zip_path):
                try: os.remove(zip_path)
                except: pass
            if os.path.exists(extract_path):
                try: shutil.rmtree(extract_path)
                except: pass
            
            error_msg = str(e)
            self.after(0, lambda: self._ffmpeg_install_finished(False, f"설치 오류: {error_msg}"))

    def _ffmpeg_install_finished(self, success, message):
        self.check_ffmpeg()
        if success:
            messagebox.showinfo("FFmpeg 자동 설치 완료", "FFmpeg가 정상적으로 설치 및 연동되었습니다!\n이제 고화질 영상 다운로드를 이용할 수 있습니다.")
        else:
            self.ffmpeg_install_btn.configure(state="normal", text="FFmpeg 자동 설치")
            messagebox.showerror("FFmpeg 설치 실패", f"설치 중 문제가 발생했습니다.\n\n오류 내용:\n{message}")

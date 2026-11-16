import ctypes
import os
import threading
import winsound
from typing import Optional

try:
    import nvwave as nvdaWave
except ImportError:
    nvdaWave = None
try:
    import globalPluginHandler, tones
except ImportError:
    globalPluginHandler = tones = None


class RecordingBridge:
    def __init__(self, default_intro: Optional[str] = None):
        self.default_intro = default_intro
        self.is_recording = False

    def _async(self, fn, *args) -> None:
        threading.Thread(target=fn, args=args, daemon=True).start()

    def play_rules_intro(self, audio_path: Optional[str] = None) -> bool:
        path = audio_path or self.default_intro
        if not path or not os.path.isfile(path):
            return False
        ext = os.path.splitext(path)[1].lower()
        if ext == ".wav":
            if nvdaWave and hasattr(nvdaWave, "playWaveFile"):
                self._async(nvdaWave.playWaveFile, path)
            else:
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return True
        if ext == ".mp3":
            def _play_mp3(p: str) -> None:
                mci = ctypes.windll.winmm.mciSendStringW
                mci("close intro_clip", None, 0, None)
                mci(f'open "{p}" type mpegvideo alias intro_clip', None, 0, None)
                mci("play intro_clip", None, 0, None)

            self._async(_play_mp3, path)
            return True
        return False

    def _dispatch_recording(self, action: str, freq: int) -> None:
        if globalPluginHandler:
            for plugin in getattr(globalPluginHandler, "runningPlugins", []):
                script = getattr(plugin, f"script_{action}Recording", None)
                if callable(script):
                    self._async(script, None)
                    return
        self._async(tones.beep if tones else winsound.Beep, freq, 150)

    def trigger_recording_start(self) -> bool:
        if self.is_recording:
            return False
        self.is_recording = True
        self._dispatch_recording("start", 880)
        return True

    def trigger_recording_stop(self) -> bool:
        if not self.is_recording:
            return False
        self.is_recording = False
        self._dispatch_recording("stop", 440)
        return True

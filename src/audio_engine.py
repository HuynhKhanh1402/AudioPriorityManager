import time
import threading
from typing import Dict, Tuple, Optional, Callable
from dataclasses import dataclass

try:
    from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioMeterInformation
    from comtypes import CLSCTX_ALL
except Exception as e:
    print("Missing dependencies. Please install with:")
    print("  pip install pycaw comtypes")
    exit(1)

@dataclass
class AudioDuckingConfig:
    priority_process: str
    other_processes: Optional[list] = None
    duck_to: float = 0.25
    threshold: float = 0.02
    priority_attack_threshold: float = 0.06
    priority_release_threshold: float = 0.02
    attack_frames: int = 3
    release_frames: int = 20
    min_overlap_frames: int = 2
    interval: float = 0.05
    step: float = 0.08

class AudioDuckingEngine:
    def __init__(self, config: AudioDuckingConfig, status_callback: Optional[Callable] = None):
        self.config = config
        self.status_callback = status_callback
        self.running = False
        self.thread = None
        
        # State
        self.original: Dict[str, float] = {}
        self.overlap_cnt: Dict[str, int] = {}
        self.priority_active = False
        self.pri_attack = 0
        self.pri_release = 0
        
        # Validation
        self._validate_config()
    
    def _validate_config(self):
        """Validate and clamp configuration values"""
        self.config.duck_to = self._clamp(self.config.duck_to, 0.0, 1.0)
        self.config.threshold = self._clamp(self.config.threshold, 0.0, 1.0)
        self.config.priority_attack_threshold = self._clamp(self.config.priority_attack_threshold, 0.0, 1.0)
        self.config.priority_release_threshold = self._clamp(self.config.priority_release_threshold, 0.0, 1.0)
        self.config.interval = max(0.02, self.config.interval)
        self.config.step = self._clamp(self.config.step, 0.01, 1.0)
        self.config.attack_frames = max(1, self.config.attack_frames)
        self.config.release_frames = max(1, self.config.release_frames)
        self.config.min_overlap_frames = max(1, self.config.min_overlap_frames)

    def _clamp(self, x: float, lo: float, hi: float) -> float:
        return lo if x < lo else hi if x > hi else x

    def _get_interfaces(self, session) -> Tuple[Optional[ISimpleAudioVolume], Optional[IAudioMeterInformation]]:
        try:
            vol = session._ctl.QueryInterface(ISimpleAudioVolume)
            meter = session._ctl.QueryInterface(IAudioMeterInformation)
            return vol, meter
        except Exception:
            return None, None

    def start(self):
        """Start the audio ducking engine"""
        if self.running:
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self._notify_status("started", f"Audio ducking started for {self.config.priority_process}")
        return True

    def stop(self):
        """Stop the audio ducking engine and restore volumes"""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        
        self._restore_all_volumes()
        self._notify_status("stopped", "Audio ducking stopped, volumes restored")

    def _notify_status(self, status: str, message: str):
        """Notify status callback if available"""
        if self.status_callback:
            try:
                self.status_callback(status, message, {
                    'priority_active': self.priority_active,
                    'ducked_sessions': len([k for k, v in self.overlap_cnt.items() if v >= self.config.min_overlap_frames])
                })
            except Exception:
                pass

    def _restore_all_volumes(self):
        """Restore all saved original volumes"""
        try:
            sessions = AudioUtilities.GetAllSessions()
            for s in sessions:
                try:
                    if not s.Process:
                        continue
                    key = s.InstanceIdentifier
                    vol, _ = self._get_interfaces(s)
                    if not vol or key not in self.original:
                        continue
                    
                    target = self._clamp(self.original[key], 0.0, 1.0)
                    vol.SetMasterVolume(target, None)
                except Exception:
                    continue
        except Exception:
            pass

    def _run_loop(self):
        """Main audio ducking loop"""
        priority_name = self.config.priority_process.lower()
        limit_to = [name.lower() for name in self.config.other_processes] if self.config.other_processes else None
        
        while self.running:
            try:
                sessions = AudioUtilities.GetAllSessions()
            except Exception:
                time.sleep(self.config.interval)
                continue

            # === Evaluate priority sessions ===
            pri_peak = 0.0
            pri_sessions = []
            
            for s in sessions:
                try:
                    if not s.Process:
                        continue
                    if s.Process.name().lower() == priority_name:
                        pri_sessions.append(s)
                except Exception:
                    continue

            # Get peak from all priority sessions
            for s in pri_sessions:
                _, meter = self._get_interfaces(s)
                if meter is None:
                    continue
                try:
                    v = meter.GetPeakValue()
                    if v is None:
                        v = 0.0
                except Exception:
                    v = 0.0
                if v > pri_peak:
                    pri_peak = v

            # Hysteresis / debouncing logic
            if pri_peak >= self.config.priority_attack_threshold:
                self.pri_attack = min(self.config.attack_frames, self.pri_attack + 1)
                self.pri_release = 0
            elif pri_peak <= self.config.priority_release_threshold:
                self.pri_release = min(self.config.release_frames, self.pri_release + 1)
                self.pri_attack = 0
            else:
                # Between thresholds: decay slowly
                self.pri_attack = max(0, self.pri_attack - 1)
                self.pri_release = max(0, self.pri_release - 1)

            # Update priority active state
            old_priority_active = self.priority_active
            if not self.priority_active and self.pri_attack >= self.config.attack_frames:
                self.priority_active = True
            elif self.priority_active and self.pri_release >= self.config.release_frames:
                self.priority_active = False

            # Notify if priority state changed
            if old_priority_active != self.priority_active:
                self._notify_status("priority_changed", 
                    f"Priority {'activated' if self.priority_active else 'deactivated'}")

            # === Duck / restore other sessions ===
            live_keys = set()
            
            for s in sessions:
                try:
                    if not s.Process:
                        continue
                    pname = s.Process.name().lower()
                    if pname == priority_name:
                        continue
                    if limit_to is not None and pname not in limit_to:
                        continue

                    vol, meter = self._get_interfaces(s)
                    if vol is None or meter is None:
                        continue

                    key = s.InstanceIdentifier
                    live_keys.add(key)

                    # Save original volume once
                    if key not in self.original:
                        try:
                            self.original[key] = vol.GetMasterVolume()
                        except Exception:
                            self.original[key] = 1.0

                    try:
                        peak = meter.GetPeakValue()
                        if peak is None:
                            peak = 0.0
                    except Exception:
                        peak = 0.0

                    # Track overlap only when priority is active
                    if self.priority_active and peak > self.config.threshold:
                        self.overlap_cnt[key] = min(self.config.min_overlap_frames, 
                                                  self.overlap_cnt.get(key, 0) + 1)
                    else:
                        # Decay overlap counter
                        self.overlap_cnt[key] = max(0, self.overlap_cnt.get(key, 0) - 1)

                    # Decide target volume
                    if self.priority_active and self.overlap_cnt.get(key, 0) >= self.config.min_overlap_frames:
                        target = self.config.duck_to
                    else:
                        target = self.original.get(key, 1.0)

                    # Smooth fade to target
                    try:
                        cur = vol.GetMasterVolume()
                        if cur is None:
                            cur = 1.0
                        
                        if abs(cur - target) < 0.01:
                            vol.SetMasterVolume(target, None)
                        else:
                            nextv = cur + self._clamp(target - cur, -self.config.step, self.config.step)
                            vol.SetMasterVolume(self._clamp(nextv, 0.0, 1.0), None)
                    except Exception:
                        pass

                except Exception:
                    continue

            # Cleanup stale entries
            stale = set(self.original.keys()) - live_keys
            for k in stale:
                self.original.pop(k, None)
                self.overlap_cnt.pop(k, None)

            time.sleep(self.config.interval)

    def get_status(self) -> dict:
        """Get current engine status"""
        return {
            'running': self.running,
            'priority_active': self.priority_active,
            'priority_process': self.config.priority_process,
            'ducked_sessions': len([k for k, v in self.overlap_cnt.items() 
                                  if v >= self.config.min_overlap_frames]),
            'total_sessions': len(self.original)
        }

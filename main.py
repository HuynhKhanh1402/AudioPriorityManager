#!/usr/bin/env python3
"""
Audio Priority Manager - Legacy CLI version
This is the original implementation. For the new version with GUI, use app.py instead.
"""

import time
import argparse
import atexit
import sys
from typing import Dict, Tuple, Optional

try:
    from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume, IAudioMeterInformation
    from comtypes import CLSCTX_ALL
except Exception as e:
    print("Missing dependencies. Please install with:")
    print("  pip install pycaw comtypes")
    print("Or run the new version: python app.py")
    sys.exit(1)

def get_interfaces(session) -> Tuple[Optional[ISimpleAudioVolume], Optional[IAudioMeterInformation]]:
    try:
        vol = session._ctl.QueryInterface(ISimpleAudioVolume)  # type: ignore[attr-defined]
        meter = session._ctl.QueryInterface(IAudioMeterInformation)  # type: ignore[attr-defined]
        return vol, meter
    except Exception:
        return None, None

def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def main():
    parser = argparse.ArgumentParser(description="Ducking non-priority audio sessions on Windows (WASAPI/pycaw) with hysteresis.")
    parser.add_argument("--priority", required=True, help='Priority process EXE name, e.g. "vlc.exe"')
    parser.add_argument("--other", nargs="*", default=None, help='Optional list of specific non-priority EXE names to duck; if omitted, duck all non-priority sessions')
    parser.add_argument("--duck-to", type=float, default=0.25, help="Target volume for ducked sessions (0.0-1.0). Default 0.25")
    parser.add_argument("--threshold", type=float, default=0.02, help="Peak threshold for NON-priority sessions to count as playing (0.0-1.0). Default 0.02 (~-34 dBFS)")
    # Hysteresis & debouncing for priority session
    parser.add_argument("--priority-attack-threshold", type=float, default=0.06, help="Priority attack threshold to start ducking (0.0-1.0). Default 0.06 (~-24 dBFS)")
    parser.add_argument("--priority-release-threshold", type=float, default=0.02, help="Priority release threshold to stop ducking (0.0-1.0). Default 0.02 (~-34 dBFS)")
    parser.add_argument("--attack-frames", type=int, default=3, help="Consecutive frames priority must exceed attack threshold to start ducking. Default 3")
    parser.add_argument("--release-frames", type=int, default=20, help="Consecutive frames priority must stay below release threshold to stop ducking. Default 20")
    # Overlap requirement to avoid ducking others if they only blip once
    parser.add_argument("--min-overlap-frames", type=int, default=2, help="Consecutive frames non-priority must be active (while priority is active) before ducking. Default 2")
    parser.add_argument("--interval", type=float, default=0.05, help="Polling interval in seconds. Default 0.05s")
    parser.add_argument("--step", type=float, default=0.08, help="Fade step per tick (0.0-1.0). Default 0.08")
    args = parser.parse_args()

    priority_name = args.priority.lower()
    limit_to = [name.lower() for name in args.other] if args.other else None
    duck_to = clamp(args.duck_to, 0.0, 1.0)
    other_threshold = clamp(args.threshold, 0.0, 1.0)
    p_attack_th = clamp(args.priority_attack_threshold, 0.0, 1.0)
    p_release_th = clamp(args.priority_release_threshold, 0.0, 1.0)
    interval = max(0.02, args.interval)
    step = clamp(args.step, 0.01, 1.0)

    attack_frames = max(1, args.attack_frames)
    release_frames = max(1, args.release_frames)
    min_overlap_frames = max(1, args.min_overlap_frames)

    # State
    original: Dict[str, float] = {}           # session.InstanceIdentifier -> original volume
    overlap_cnt: Dict[str, int] = {}          # for each non-priority session
    priority_active = False
    pri_attack = 0
    pri_release = 0

    def restore_all():
        # Restore any saved volumes on exit.
        try:
            sessions = AudioUtilities.GetAllSessions()
        except Exception:
            return
        for s in sessions:
            try:
                if not s.Process:
                    continue
                key = s.InstanceIdentifier
                vol, _ = get_interfaces(s)
                if not vol:
                    continue
                if key in original:
                    target = clamp(original[key], 0.0, 1.0)
                    try:
                        vol.SetMasterVolume(target, None)
                    except Exception:
                        pass
            except Exception:
                continue

    atexit.register(restore_all)

    print("[*] Running ducking loop. Priority:", priority_name)
    print("[*] Press Ctrl+C to stop; volumes will be restored.")

    try:
        while True:
            try:
                sessions = AudioUtilities.GetAllSessions()
            except Exception:
                time.sleep(interval)
                continue

            # === Evaluate priority ===
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

            for s in pri_sessions:
                _, meter = get_interfaces(s)
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

            # Hysteresis / debouncing: attack & release counters
            if pri_peak >= p_attack_th:
                pri_attack = min(attack_frames, pri_attack + 1)
                pri_release = 0
            elif pri_peak <= p_release_th:
                pri_release = min(release_frames, pri_release + 1)
                pri_attack = 0
            else:
                # Between thresholds: decay slowly
                pri_attack = max(0, pri_attack - 1)
                pri_release = max(0, pri_release - 1)

            if not priority_active and pri_attack >= attack_frames:
                priority_active = True
            elif priority_active and pri_release >= release_frames:
                priority_active = False

            # === Duck / restore others ===
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

                    vol, meter = get_interfaces(s)
                    if vol is None or meter is None:
                        continue

                    key = s.InstanceIdentifier
                    live_keys.add(key)

                    # Save original volume once
                    if key not in original:
                        try:
                            original[key] = vol.GetMasterVolume()
                        except Exception:
                            original[key] = 1.0

                    try:
                        peak = meter.GetPeakValue()
                        if peak is None:
                            peak = 0.0
                    except Exception:
                        peak = 0.0

                    # Track overlap only when priority is active
                    if priority_active and peak > other_threshold:
                        overlap_cnt[key] = min(min_overlap_frames, overlap_cnt.get(key, 0) + 1)
                    else:
                        # decay overlap counter so short gaps don't instantly restore/duck
                        overlap_cnt[key] = max(0, overlap_cnt.get(key, 0) - 1)

                    # Decide target
                    if priority_active and overlap_cnt.get(key, 0) >= min_overlap_frames:
                        target = duck_to
                    else:
                        target = original.get(key, 1.0)

                    # Smooth fade
                    try:
                        cur = vol.GetMasterVolume()
                        if cur is None:
                            cur = 1.0
                        if abs(cur - target) < 0.01:
                            vol.SetMasterVolume(target, None)
                        else:
                            nextv = cur + clamp(target - cur, -step, step)
                            vol.SetMasterVolume(clamp(nextv, 0.0, 1.0), None)
                    except Exception:
                        pass

                except Exception:
                    continue

            # Cleanup maps
            stale = set(original.keys()) - live_keys
            for k in stale:
                original.pop(k, None)
                overlap_cnt.pop(k, None)

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n[!] Stopping and restoring volumes...")
        restore_all()
        print("[*] Done.")

if __name__ == "__main__":
    main()

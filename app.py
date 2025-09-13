#!/usr/bin/env python3
"""
Audio Priority Manager - Main Application Launcher

This application provides audio ducking functionality for Windows.
It can be run as a GUI application or command-line tool.
"""

import sys
import argparse
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def run_gui():
    """Run the GUI version of the application"""
    try:
        from src.gui import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"Failed to import GUI components: {e}")
        print("Make sure PyQt6 is installed: pip install PyQt6")
        sys.exit(1)

def run_cli():
    """Run the command-line version (original functionality)"""
    from src.audio_engine import AudioDuckingEngine, AudioDuckingConfig
    import time
    import atexit
    
    parser = argparse.ArgumentParser(description="Audio ducking for priority processes on Windows")
    parser.add_argument("--priority", required=True, help='Priority process EXE name, e.g. "vlc.exe"')
    parser.add_argument("--other", nargs="*", default=None, help='Optional list of specific non-priority EXE names to duck')
    parser.add_argument("--duck-to", type=float, default=0.25, help="Target volume for ducked sessions (0.0-1.0). Default 0.25")
    parser.add_argument("--threshold", type=float, default=0.02, help="Peak threshold for non-priority sessions (0.0-1.0). Default 0.02")
    parser.add_argument("--priority-attack-threshold", type=float, default=0.06, help="Priority attack threshold (0.0-1.0). Default 0.06")
    parser.add_argument("--priority-release-threshold", type=float, default=0.02, help="Priority release threshold (0.0-1.0). Default 0.02")
    parser.add_argument("--attack-frames", type=int, default=3, help="Attack frames. Default 3")
    parser.add_argument("--release-frames", type=int, default=20, help="Release frames. Default 20")
    parser.add_argument("--min-overlap-frames", type=int, default=2, help="Min overlap frames. Default 2")
    parser.add_argument("--interval", type=float, default=0.05, help="Polling interval in seconds. Default 0.05")
    parser.add_argument("--step", type=float, default=0.08, help="Fade step per tick. Default 0.08")
    
    args = parser.parse_args()
    
    # Create configuration
    config = AudioDuckingConfig(
        priority_process=args.priority,
        other_processes=args.other,
        duck_to=args.duck_to,
        threshold=args.threshold,
        priority_attack_threshold=args.priority_attack_threshold,
        priority_release_threshold=args.priority_release_threshold,
        attack_frames=args.attack_frames,
        release_frames=args.release_frames,
        min_overlap_frames=args.min_overlap_frames,
        interval=args.interval,
        step=args.step
    )
    
    def status_callback(status, message, data):
        print(f"[{status.upper()}] {message}")
    
    # Create and start engine
    engine = AudioDuckingEngine(config, status_callback)
    
    def cleanup():
        print("\n[!] Stopping and restoring volumes...")
        engine.stop()
        print("[*] Done.")
    
    atexit.register(cleanup)
    
    print("[*] Starting audio ducking engine...")
    print(f"[*] Priority process: {args.priority}")
    print("[*] Press Ctrl+C to stop.")
    
    if engine.start():
        try:
            while engine.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        print("[!] Failed to start engine.")
        sys.exit(1)

def main():
    """Main entry point"""
    # Check if GUI should be used (default) or CLI
    if len(sys.argv) == 1:
        # No arguments - run GUI
        run_gui()
    elif '--gui' in sys.argv:
        # Explicit GUI request
        sys.argv.remove('--gui')
        run_gui()
    elif '--help' in sys.argv or '-h' in sys.argv:
        # Show help for both modes
        print("Audio Priority Manager")
        print("=" * 50)
        print("Usage:")
        print("  python app.py                    # Run GUI mode (default)")
        print("  python app.py --gui              # Run GUI mode explicitly")
        print("  python app.py --priority vlc.exe # Run CLI mode")
        print("")
        print("GUI Mode:")
        print("  Interactive graphical interface with system tray support")
        print("")
        print("CLI Mode:")
        run_cli()
    else:
        # CLI mode with arguments
        run_cli()

if __name__ == "__main__":
    main()

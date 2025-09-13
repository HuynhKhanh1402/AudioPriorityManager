"""
Process manager for detecting running processes and their audio activity
"""
import psutil
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

try:
    from pycaw.pycaw import AudioUtilities
except ImportError:
    AudioUtilities = None

@dataclass
class ProcessInfo:
    pid: int
    name: str
    exe_name: str
    has_audio: bool
    audio_level: float = 0.0
    description: str = ""

class ProcessManager:
    def __init__(self):
        self.cached_processes = {}
        
    def get_running_processes(self) -> List[ProcessInfo]:
        """Get list of running processes with audio information"""
        processes = []
        audio_processes = self._get_audio_processes()
        
        # Get all running processes
        seen_names = set()
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                proc_info = proc.info
                if not proc_info['name'] or proc_info['name'] == '':
                    continue
                
                pid = proc_info['pid']
                name = proc_info['name']
                exe_name = name.lower()
                
                # Skip system processes and duplicates
                if (exe_name in ['system', 'registry', 'smss.exe', 'csrss.exe', 'wininit.exe', 
                               'winlogon.exe', 'services.exe', 'lsass.exe', 'svchost.exe',
                               'dwm.exe', 'explorer.exe'] or 
                    exe_name in seen_names):
                    continue
                
                seen_names.add(exe_name)
                
                # Check if this process has audio
                has_audio = exe_name in audio_processes
                audio_level = audio_processes.get(exe_name, 0.0)
                
                # Get description if available
                description = self._get_process_description(proc)
                
                process_info = ProcessInfo(
                    pid=pid,
                    name=name,
                    exe_name=exe_name,
                    has_audio=has_audio,
                    audio_level=audio_level,
                    description=description
                )
                
                processes.append(process_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Sort: audio processes first, then by name
        processes.sort(key=lambda x: (not x.has_audio, x.name.lower()))
        
        return processes
    
    def _get_audio_processes(self) -> Dict[str, float]:
        """Get processes that are currently playing audio"""
        audio_processes = {}
        
        if AudioUtilities is None:
            return audio_processes
        
        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                try:
                    if session.Process and session.Process.name():
                        proc_name = session.Process.name().lower()
                        
                        # Get audio level
                        peak = 0.0
                        try:
                            # Get meter interface for audio level
                            from pycaw.pycaw import IAudioMeterInformation
                            meter = session._ctl.QueryInterface(IAudioMeterInformation)
                            peak_value = meter.GetPeakValue()
                            peak = peak_value if peak_value is not None else 0.0
                        except Exception:
                            # If we can't get audio level, just mark as having audio session
                            peak = 0.0
                        
                        # Store the highest peak for this process
                        if proc_name not in audio_processes or peak > audio_processes[proc_name]:
                            audio_processes[proc_name] = peak
                            
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return audio_processes
    
    def _get_process_description(self, proc) -> str:
        """Get process description/title if available"""
        try:
            proc_name = proc.name().lower()
            
            # Common process descriptions mapping
            descriptions = {
                # Browsers
                'chrome.exe': 'Google Chrome',
                'firefox.exe': 'Mozilla Firefox',
                'msedge.exe': 'Microsoft Edge',
                'edge.exe': 'Microsoft Edge',
                'opera.exe': 'Opera Browser',
                'brave.exe': 'Brave Browser',
                'safari.exe': 'Safari',
                'iexplore.exe': 'Internet Explorer',
                
                # Communication
                'discord.exe': 'Discord',
                'teams.exe': 'Microsoft Teams',
                'zoom.exe': 'Zoom Video Communications',
                'skype.exe': 'Skype',
                'telegram.exe': 'Telegram Desktop',
                'whatsapp.exe': 'WhatsApp Desktop',
                'slack.exe': 'Slack',
                'teamviewer.exe': 'TeamViewer',
                
                # Media Players
                'spotify.exe': 'Spotify Music',
                'vlc.exe': 'VLC Media Player',
                'potplayer.exe': 'PotPlayer',
                'potplayermini64.exe': 'PotPlayer Mini',
                'mpc-hc.exe': 'Media Player Classic',
                'mpc-hc64.exe': 'Media Player Classic (64-bit)',
                'wmplayer.exe': 'Windows Media Player',
                'itunes.exe': 'Apple iTunes',
                'foobar2000.exe': 'foobar2000 Audio Player',
                'winamp.exe': 'Winamp Media Player',
                'musicbee.exe': 'MusicBee',
                'aimp.exe': 'AIMP Audio Player',
                'deezer.exe': 'Deezer Music',
                'tidal.exe': 'TIDAL Music',
                'amazon music.exe': 'Amazon Music',
                'apple music.exe': 'Apple Music',
                
                # Streaming/Recording
                'obs64.exe': 'OBS Studio (64-bit)',
                'obs32.exe': 'OBS Studio (32-bit)',
                'obs.exe': 'OBS Studio',
                'streamlabs obs.exe': 'Streamlabs OBS',
                'xsplit.exe': 'XSplit Broadcaster',
                'bandicam.exe': 'Bandicam Screen Recorder',
                'fraps.exe': 'Fraps',
                
                # Gaming
                'steam.exe': 'Steam Gaming Platform',
                'epicgameslauncher.exe': 'Epic Games Launcher',
                'origin.exe': 'EA Origin',
                'uplay.exe': 'Ubisoft Connect',
                'battlenet.exe': 'Blizzard Battle.net',
                'gog galaxy.exe': 'GOG Galaxy',
                'minecraft.exe': 'Minecraft',
                'roblox.exe': 'Roblox',
                
                # Development Tools
                'notepad.exe': 'Windows Notepad',
                'notepad++.exe': 'Notepad++ Text Editor',
                'code.exe': 'Visual Studio Code',
                'devenv.exe': 'Microsoft Visual Studio',
                'pycharm64.exe': 'JetBrains PyCharm',
                'idea64.exe': 'IntelliJ IDEA',
                'sublime_text.exe': 'Sublime Text',
                'atom.exe': 'Atom Editor',
                
                # Audio Production
                'audacity.exe': 'Audacity Audio Editor',
                'reaper.exe': 'REAPER Digital Audio Workstation',
                'fl64.exe': 'FL Studio',
                'cubase.exe': 'Steinberg Cubase',
                'ableton live.exe': 'Ableton Live',
                'logic pro.exe': 'Logic Pro',
                
                # Office & Productivity
                'winword.exe': 'Microsoft Word',
                'excel.exe': 'Microsoft Excel',
                'powerpnt.exe': 'Microsoft PowerPoint',
                'outlook.exe': 'Microsoft Outlook',
                'onenote.exe': 'Microsoft OneNote',
                'notion.exe': 'Notion Workspace',
                
                # System & Utilities
                'explorer.exe': 'Windows Explorer',
                'taskmgr.exe': 'Task Manager',
                'cmd.exe': 'Command Prompt',
                'powershell.exe': 'Windows PowerShell',
                'calculator.exe': 'Calculator',
                'mspaint.exe': 'Microsoft Paint',
                
                # Security
                'mbam.exe': 'Malwarebytes Anti-Malware',
                'avast.exe': 'Avast Antivirus',
                'avgui.exe': 'AVG Antivirus',
                'norton.exe': 'Norton Security',
            }
            
            # Return description if found, otherwise return empty string
            return descriptions.get(proc_name, "")
            
        except Exception:
            return ""
    
    def get_common_audio_processes(self) -> List[str]:
        """Get list of common audio applications"""
        return [
            # Media Players
            "vlc.exe",
            "potplayer.exe",
            "potplayermini64.exe",
            "mpc-hc.exe",
            "mpc-hc64.exe",
            "wmplayer.exe",
            "kmplayer.exe",
            
            # Music Applications
            "spotify.exe", 
            "itunes.exe",
            "apple music.exe",
            "deezer.exe",
            "tidal.exe",
            "amazon music.exe",
            "youtube music.exe",
            "winamp.exe",
            "foobar2000.exe",
            "musicbee.exe",
            "aimp.exe",
            
            # Browsers (often play audio)
            "chrome.exe",
            "firefox.exe",
            "edge.exe",
            "msedge.exe",
            "opera.exe",
            "brave.exe",
            
            # Communication
            "discord.exe",
            "teams.exe",
            "zoom.exe",
            "skype.exe",
            "telegram.exe",
            "whatsapp.exe",
            "slack.exe",
            
            # Streaming/Recording
            "obs64.exe",
            "obs32.exe",
            "obs.exe",
            "streamlabs obs.exe",
            "xsplit.exe",
            "bandicam.exe",
            "fraps.exe",
            
            # Games/Gaming
            "steam.exe",
            "epicgameslauncher.exe",
            "origin.exe",
            "uplay.exe",
            "battlenet.exe",
            "gog galaxy.exe",
            
            # Audio Tools
            "audacity.exe",
            "reaper.exe",
            "fl64.exe",
            "cubase.exe",
            "ableton live.exe"
        ]

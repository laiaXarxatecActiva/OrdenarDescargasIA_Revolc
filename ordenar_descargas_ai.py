#!/usr/bin/env python3
"""
AI-based Download Organizer using OpenClaw agent capabilities.
This is the AI version of the download organizer, while sort-downloads.sh
remains the fallback script.
"""

import os
import time
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Optional, Tuple
import threading
import queue
import sys

# Configuration
CONFIG = {
    "DOWNLOAD_DIR": "",  # Will be auto-detected
    "LOG_FILE": "organizar_descargas.log",
    "CATEGORIES": {
        "Audio": ["mp3", "wav", "flac", "aac", "ogg", "m4a", "wma", "opus", "pkf", "tts", "wpl", "ape", ".pls"],
        "Video": ["mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v"],
        "PDFs": ["pdf"],
        "Documentos": ["odt", "doc", "docx", "txt", "rtf", "xls", "xlsx", "ppt", "pptx", "csv", "ods", "odp", "md"],
        "Imagenes": ["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "tiff", "ico"],
        "Comprimidos": ["zip", "rar", "7z", "tar", "gz", "xz", "bz2"],
        "Instaladores": ["appimage", "deb", "rpm", "sh", "run"],
    },
    "IGNORE_EXTENSIONS": ["crdownload", "part", "tmp", "download"],
    "FALLBACK_CATEGORY": "Otros",
    "STABILITY_CHECK_TRIES": 40,
    "STABILITY_CHECK_DELAY": 0.5,
    "MAX_FILENAME_LENGTH": 255,
}

class DownloadOrganizerAI:
    def __init__(self):
        self.download_dir = self._get_download_dir()
        self.log_file = self._get_log_file_path()
        self.category_map = self._build_category_map()
        self.ignore_map = {ext.lower(): 1 for ext in CONFIG["IGNORE_EXTENSIONS"]}
        self.running = True
        self.lock_file = self._get_lock_file()
        self.lock = threading.Lock()
        self.process_watches = {}

    def _get_download_dir(self) -> str:
        """Auto-detect user's Downloads folder"""
        import subprocess
        try:
            result = subprocess.run(['xdg-user-dir', 'DOWNLOAD'],
                                  capture_output=True, text=True, check=True)
            path = result.stdout.strip()
            if path and os.path.exists(path) and path != os.path.expanduser('~'):
                return path
        except:
            pass

        home = os.path.expanduser('~')
        for candidate in ['Descargas', 'Downloads']:
            path = os.path.join(home, candidate)
            if os.path.exists(path):
                return path

        return os.path.join(home, 'Downloads')

    def _get_log_file_path(self) -> str:
        """Get log file path (outside downloads folder)"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, CONFIG['LOG_FILE'])

    def _get_lock_file(self) -> str:
        """Get file-based lock to prevent multiple instances"""
        xdg_runtime = os.environ.get('XDG_RUNTIME_DIR', '/tmp')
        return os.path.join(xdg_runtime, 'ordenar-descargas-ai.lock')

    def _build_category_map(self) -> Dict[str, str]:
        """Build extension to category mapping"""
        category_map = {}
        for category, extensions in CONFIG['CATEGORIES'].items():
            for ext in extensions:
                category_map[ext.lower()] = category
        return category_map

    def log_event(self, message: str):
        """Log event with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"{timestamp} | {message}\n"
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            print(f"Failed to write to log: {e}")

    def wait_until_stable(self, file_path: str) -> bool:
        """Wait until file size and modification time stabilize"""
        tries = 0
        max_tries = CONFIG['STABILITY_CHECK_TRIES']
        delay = CONFIG['STABILITY_CHECK_DELAY']

        prev = ""
        while tries < max_tries:
            try:
                if not os.path.exists(file_path):
                    return False

                stat = os.stat(file_path)
                cur = f"{stat.st_size}-{stat.st_mtime}"

                if cur == prev:
                    return True

                prev = cur
                tries += 1
                time.sleep(delay)

            except Exception:
                return False

        self.log_event(f"AVISO: '{os.path.basename(file_path)}' no terminó de escribirse a tiempo, se omite")
        return False

    def generate_dest_name(self, dest_dir: str, filename: str) -> str:
        """Generate unique destination filename"""
        if len(filename) > CONFIG['MAX_FILENAME_LENGTH']:
            name_part = filename[:CONFIG['MAX_FILENAME_LENGTH'] - 10]
            ext_part = filename[CONFIG['MAX_FILENAME_LENGTH'] - 10:]
        else:
            name_part, ext_part = os.path.splitext(filename)

        dest_name = filename
        counter = 1

        while True:
            dest_path = os.path.join(dest_dir, dest_name)
            if not os.path.exists(dest_path):
                break

            counter += 1
            dest_name = f"{name_part}_{counter}{ext_part}"

        return dest_name

    def categorize_file(self, filename: str) -> str:
        """Categorize file based on extension"""
        ext = ""
        if '.' in filename:
            ext = filename.split('.')[-1].lower()

        if not ext:
            return CONFIG['FALLBACK_CATEGORY']

        if ext in self.ignore_map:
            return ""

        return self.category_map.get(ext, CONFIG['FALLBACK_CATEGORY'])

    def ensure_dirs_exist(self):
        """Create download dir and all category subfolders"""
        os.makedirs(self.download_dir, exist_ok=True)

        for category in list(CONFIG['CATEGORIES'].keys()) + [CONFIG['FALLBACK_CATEGORY']]:
            category_dir = os.path.join(self.download_dir, category)
            os.makedirs(category_dir, exist_ok=True)

    def process_file(self, file_path: str):
        """Process a single file (AI-based organizer)"""
        try:
            filename = os.path.basename(file_path)

            # Skip hidden files
            if filename.startswith('.'):
                return

            # Check if it's a regular file
            if not os.path.isfile(file_path):
                return

            # Check if it's a symlink
            if os.path.islink(file_path):
                return

            category = self.categorize_file(filename)

            if not category:
                self.log_event(f"IGNORADO: '{filename}' (descarga en curso)")
                return

            if not self.wait_until_stable(file_path):
                return

            dest_dir = os.path.join(self.download_dir, category)
            dest_name = self.generate_dest_name(dest_dir, filename)
            dest_path = os.path.join(dest_dir, dest_name)

            try:
                os.rename(file_path, dest_path)
                self.log_event(f"OK: {filename} -> {category}/{dest_name}")
            except Exception as e:
                self.log_event(f"ERROR: no se pudo mover '{filename}' a {category}/ - {e}")

        except Exception as e:
            self.log_event(f"ERROR processing file '{os.path.basename(file_path)}': {e}")

    def check_existing_files(self):
        """Process files that already exist in download dir"""
        try:
            for item in os.listdir(self.download_dir):
                item_path = os.path.join(self.download_dir, item)
                if os.path.isfile(item_path):
                    self.process_file(item_path)
        except Exception as e:
            self.log_event(f"ERROR scanning existing files: {e}")

    def run_forever(self):
        """Main organizer loop"""
        try:
            # Set up simple file system monitoring
            self.log_event("=== Iniciando organizador de descargas AI ===")
            self.log_event(f"Vigilando: {self.download_dir}")

            self.ensure_dirs_exist()

            # Check existing files
            self.check_existing_files()

            # Use inotifywait for efficient file monitoring
            import subprocess

            # Check if inotifywait is available
            try:
                subprocess.run(['which', 'inotifywait'], check=True, capture_output=True)
                has_inotify = True
            except:
                has_inotify = False

            if has_inotify:
                self.log_event("Usando inotifywait para vigilancia en tiempo real")
                # Use inotifywait like the bash script
                cmd = ['inotifywait', '-m', '-q', '-e', 'close_write', '-e', 'moved_to',
                      '--format', '%w%f', self.download_dir]

                process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, text=True)

                try:
                    while self.running:
                        line = process.stdout.readline()
                        if line:
                            file_path = line.strip()
                            if file_path and os.path.exists(file_path):
                                self.process_file(file_path)
                        else:
                            time.sleep(0.1)
                except KeyboardInterrupt:
                    pass
                finally:
                    process.terminate()
                    process.wait()
            else:
                # Fallback: poll method
                self.log_event("Advertencia: inotifywait no disponible, usando método de sondeo")
                while self.running:
                    try:
                        current_files = set(os.listdir(self.download_dir))
                        if hasattr(self, 'last_files'):
                            new_files = current_files - self.last_files
                            for filename in new_files:
                                self.process_file(os.path.join(self.download_dir, filename))

                        self.last_files = current_files
                        time.sleep(1)
                    except Exception as e:
                        self.log_event(f"ERROR en bucle principal: {e}")
                        time.sleep(5)

        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.log_event(f"ERROR FATAL: {e}")
        finally:
            self.log_event("El observador de archivos AI se detuvo")

    def stop(self):
        """Stop the organizer"""
        self.running = False


def main():
    """Main entry point"""
    # Check for existing lock
    lock_file = "/tmp/ordenar-descargas-ai.lock"
    if os.path.exists(lock_file):
        print("sort-downloads-ai.py ya se está ejecutando. Saliendo.")
        sys.exit(1)

    # Create lock file
    with open(lock_file, 'w') as f:
        f.write(str(os.getpid()))

    try:
        organizer = DownloadOrganizerAI()
        organizer.run_forever()
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
    except Exception as e:
        print(f"Error fatal: {e}")
    finally:
        # Clean up lock file
        try:
            os.remove(lock_file)
        except:
            pass

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import os
import subprocess
import argparse
import json
import shutil
import tempfile
from pathlib import Path

def format_size(size_bytes):
    """Helper to format bytes into a human-readable string."""
    if size_bytes >= 1024**3:
        return f"{size_bytes / (1024**3):.2f} GB"
    if size_bytes >= 1024**2:
        return f"{size_bytes / (1024**2):.2f} MB"
    else:
        return f"{size_bytes / 1024:.2f} KB"

def clean_workspace(root_dir, ignore_folders, ignore_exts):
    """Move excluded-extension files into a mirrored trash directory."""
    root_path = Path(root_dir).resolve()
    trash_path = root_path / "trash"
    ignored_extensions = {extension.lower().lstrip(".") for extension in ignore_exts}
    moved_files = 0

    for subdir, dirs, files in os.walk(root_path):
        dirs[:] = [
            directory for directory in dirs
            if directory not in ignore_folders and directory != "Z_AH" and directory != trash_path.name
        ]

        for file in files:
            source_path = Path(subdir) / file
            if source_path.suffix.lower().lstrip(".") not in ignored_extensions:
                continue

            relative_path = source_path.relative_to(root_path)
            destination_path = trash_path / relative_path
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(destination_path))
            moved_files += 1

    print(f"Moved {moved_files} file(s) to: {trash_path}")

def archive_workspace(root_dir, archive_name, ignore_folders, ignore_exts, max_size_gb, dry_run=False):
    root_path = Path(root_dir).resolve()
    # If archive_name is relative, resolve it BEFORE we change working directories
    archive_path = Path(archive_name).resolve()
    ignored_extensions = {extension.lower().lstrip(".") for extension in ignore_exts}
    max_size_bytes = max_size_gb * 1024**3
    files_to_include = []

    print(f"Scanning: {root_path}")
    if dry_run:
        print("--- DRY RUN MODE ENABLED ---")
    print(root_path)
    for subdir, dirs, files in os.walk(root_path):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if d not in ignore_folders and d != "Z_AH"]
        
        #print(files)
        for file in files:
            file_path = Path(subdir) / file
            if file_path.suffix.lower().lstrip('.') in ignored_extensions:
                continue
            
            try:
                file_size = file_path.stat().st_size
                if file_size > max_size_bytes:
                    print(f"Skipping (Too Large - {format_size(file_size)}): {file_path.name}")
                    continue
                
                # IMPORTANT: Store path RELATIVE to the root_path to avoid duplicates
                relative_path = file_path.relative_to(root_path)
                print(relative_path)
                files_to_include.append((str(relative_path), file_size))
            except OSError:
                continue

    if not files_to_include:
        print("No files matched your criteria.")
        return

    if dry_run:
        print(f"\nFiles to be included in {archive_path.name}:")
        total_bytes = 0
        for rel_path, f_size in files_to_include:
            print(f"  + [{format_size(f_size)}] {rel_path}")
            total_bytes += f_size
        
        print(f"\nSummary:")
        print(f"  Total files: {len(files_to_include)}")
        print(f"  Total size:  {format_size(total_bytes)}")
        print("\nDry run complete. No archive created.")
        return

    # Create the list file for 7-Zip
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
        for rel_path, _ in files_to_include:
            tmp.write(rel_path + "\n")
        list_file_path = tmp.name

    try:
        print(f"Creating archive: {archive_path}...")

        seven_zip = next((shutil.which(candidate) for candidate in ("7z", "7zz", "7z.exe") if shutil.which(candidate)), None)
        if seven_zip is None:
            print("Error: 7-Zip was not found in PATH. Install 7-Zip (Windows) or p7zip/7zz (Linux).")
            return

        command = [seven_zip, 'a', '-scsUTF-8', str(archive_path), f'@{list_file_path}']
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, cwd=str(root_path))
        print(f"Success! Archive created at: {archive_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during 7-Zip execution: {e}")
    except FileNotFoundError:
        print("Error: '7z' executable not found.")
    finally:
        if os.path.exists(list_file_path):
            os.remove(list_file_path)

def parse_size_limit(value):
    """Convert a size limit in GB, MB, KB, or bytes to GB."""
    if isinstance(value, (int, float)):
        return float(value)

    normalized = str(value).strip().upper()
    for suffix, divisor in (("GB", 1), ("MB", 1024), ("KB", 1024**2), ("B", 1024**3)):
        if normalized.endswith(suffix):
            return float(normalized[:-len(suffix)].strip()) / divisor
    return float(normalized)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross-platform 7z archiver.")
    parser.add_argument("config_path", nargs="?", help="JSON configuration file.")
    parser.add_argument("-i", "--input", dest="source_path", help="The source directory to archive.")
    parser.add_argument(
        "-e", "--exclude-ext", dest="ignore_exts", nargs="+",
        help="File extensions to exclude (for example: log tmp bak)."
    )
    parser.add_argument(
        "-f", "--exclude-folder", dest="ignore_folders", nargs="+",
        help="Folder names to exclude (for example: temp cache .git)."
    )
    parser.add_argument("-c", "--clean", action="store_true", help="Move excluded files to a mirrored trash directory.")
    parser.add_argument("--dry-run", action="store_true", help="List files and sizes.")
    args = parser.parse_args()

    config  = {}  
    config_path = Path(args.config_path).resolve()
    if(not config_path.exists()):
        script_dir = Path(__file__).resolve().parent
        config_path = script_dir / args.config_path
            
    else:
        try:
            with config_path.open(encoding="utf-8") as config_file:
                config = json.load(config_file)
        except (OSError, json.JSONDecodeError) as error:
            parser.error(f"could not read config file '{Path(args.config_path)}': {error}")

    # --- Configuration ---
    source_path = args.source_path or "Tools"
    source_path = Path(source_path).expanduser()
    
    OUTPUT_ARCHIVE = str(Path(source_path).resolve()) + ".7z"
    FOLDERS_TO_SKIP = set(args.ignore_folders or config.get("ignore_folders", {'temp', 'cache', '.git', '.svn', 'build', 'dist'}))
    EXTENSIONS_TO_SKIP = set(args.ignore_exts or config.get("ignore_extensions", {'log', 'tmp', 'bak', 'exe'}))
    SIZE_LIMIT_GB = parse_size_limit(config.get("size_limit", 1.0))

    if args.clean and not args.dry_run:
        clean_workspace(source_path, FOLDERS_TO_SKIP, EXTENSIONS_TO_SKIP)
        raise SystemExit(0)

    archive_workspace(source_path, OUTPUT_ARCHIVE, FOLDERS_TO_SKIP, EXTENSIONS_TO_SKIP, SIZE_LIMIT_GB, dry_run=args.dry_run)
    input("Press Enter to close...")
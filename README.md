
# ws-archiver

Cross-platform **workspace archiver and cleaner** using 7-Zip.

This tool scans a workspace, filters files by extension and size, and creates a `.7z` archive.
It can also clean a workspace by moving unwanted files into a mirrored trash directory.

## Features

- Archive filtered files
- Ignore folders
- Ignore extensions
- File size limits
- JSON configuration support
- Dry-run preview
- Clean mode with mirrored trash tree
- Linux + Windows compatible

## Installation

Clone the repo:

```bash
git clone https://github.com/yourname/ws-archiver.git
cd ws-archiver
pip install -r requirements.txt
```

## Run from Anywhere

The script automatically looks for `config.json` in its own directory, so it can
be started from any working directory.

### Linux

Make the script executable and add its directory to `PATH` for the current shell:

```bash
chmod +x /path/to/ws_archiver/ws_archiver.py
export PATH="$PATH:/path/to/ws_archiver"
```

To keep the setting after restarting the shell, add the export command to
`~/.bashrc` (or `~/.zshrc`):

```bash
echo 'export PATH="$PATH:/path/to/ws_archiver"' >> ~/.bashrc
```

You can then run it from anywhere:

```bash
ws_archiver.py --dry-run
ws_archiver.py -i /path/to/workspace -e log tmp -f .git build
```

Alternatively, use Python directly without changing `PATH`:

```bash
python3 /path/to/ws_archiver/ws_archiver.py --dry-run
```

### Windows PowerShell

Run the script from any directory by giving Python its full path:

```powershell
python C:\path\to\ws_archiver\ws_archiver.py --dry-run
python C:\path\to\ws_archiver\ws_archiver.py -i C:\path\to\workspace -c
```

To use the short `ws_archiver.py` command, add the script directory to the user
`PATH`, then open a new PowerShell window:

```powershell
$scriptDir = "C:\path\to\ws_archiver"
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";" + $scriptDir, "User")
```

## Basic Usage

```bash
ws_archiver.py -i workspace
```

Ignore folders:

```bash
ws_archiver -i workspace -f temp cache .git
```

Ignore extensions:

```bash
ws_archiver -i workspace -e log tmp bak
```

Clean mode:

```bash
ws_archiver -i workspace -c
```

JSON config:

```bash
ws_archiver config.json
```

## Requirements

- Python 3.9+
- 7-Zip installed and available in PATH

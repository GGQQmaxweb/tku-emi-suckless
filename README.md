# TKU EMI Suckless

A lightweight desktop client for Tamkang University (TKU) Educational Management Information System (EMIS).

## Features

- **Authentication**: Secure login to TKU EMIS account.
- **Student Profile**: View student details and study progress.
- **Graduation Tracker**: Calculate earned vs. required credits and track missing mandatory courses.
- **Grade History**: View course grades across all academic years.
- **Course Planner**: Search current semester courses and manage custom class schedules.
- **Offline Caching**: Caches retrieved user data locally in `.userData/`.

## Tech Stack

- **Backend & Scraper**: Python (`requests`, `beautifulsoup4`)
- **GUI Engine**: `pywebview` with HTML/CSS/JavaScript
- **Packaging**: PyInstaller

## Prerequisites

### Linux
System GTK and WebKit packages are required:
Just pick any `webkit2-4.x` you have in your distro. They're mostly inter-compatible.
- **Ubuntu/Debian**: `sudo apt install python3-gi gir1.2-webkit2-4.0` (or `gir1.2-webkit2-4.1`) 
- **Fedora**: `sudo dnf install webkit2gtk3 python3-gobject`  
- **Arch Linux**: `sudo pacman -S webkit2gtk`

### Windows
- Microsoft Edge WebView2 (default on Windows 10/11)

## Installation and Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/GGQQmaxweb/tku-emi-suckless.git
   cd tku-emi-suckless
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch the application:
   ```bash
   python main.py
   ```

## Building Executables

- **Linux**:
  ```bash
  pyinstaller tku-emi-suckless_light.spec
  ```
- **Windows**:
  ```bash
  pyinstaller --noconsole --onefile --name "tku-emi-suckless-Windows" --add-data "gui;gui" main.py
  ```
- **macOS**:
  ```bash
  pyinstaller --noconsole --onedir --name "tku-emi-suckless-macOS" --add-data "gui:gui" main.py
  ```

## License

[BEER-WARE LICENSE (Revision 42)](https://raw.githubusercontent.com/GGQQmax/tku-emi-suckless/master/LICENSE)

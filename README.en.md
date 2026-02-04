# FortiNet Log Analyzer

![Python](https://img.shields.io/badge/Python-3.x-blue.svg) ![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green.svg) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight desktop application developed in Python for viewing, analyzing, and processing Fortinet equipment logs.
It provides a user-friendly interface for security professionals to manage UTM logs without requiring a FortiAnalyzer appliance.

## Key Features

- **Graphical Log Viewer:** Load and display `.log` or `.txt` files in `key=value` format.
- **Dynamic Search:** Case-insensitive filtering across all log fields.
- **Visual Analysis:** Automatic color-coding for critical levels (alert, critical, error) and block actions (deny, block).
- **Live Statistics:** Side panel showing real-time stats (Top Source IPs, Top Actions, and Severity Levels).
- **High Performance:** Dynamic paging system (3,000 records per page) for smooth handling of large files.
- **Data Export:** Export filtered results to `.csv` or `.json` formats.
- **Detailed Inspection:** Double-click any entry to view all log metadata in a dedicated window.

## Screenshots

![Screenshot 1](./assets/screenshot-01.png)

## Quick Start

### Prerequisites
* Python 3.x

### Installation & Execution

1. **Clone the Repository**
   
   ```bash
   git clone https://github.com/solopx/fortinet-log-analyzer.git
   cd fortinet-log-analyzer
   ```
   
3. **Install Dependencies**
   
   ```bash
   pip install -r requirements.txt
   ```
   
5. **Run the App**
   
   ```bash
   python src/main.py
   ```

## Expected Log Format
The analyzer parses standard key=value log entries, such as:
```bash
date=2023-10-27 time=10:30:00 type=traffic srcip=192.168.1.10 dstip=8.8.8.8 action=deny
```

## License
Distributed under the MIT License. See LICENSE for more information.

Developed by solopx GitHub: https://github.com/solopx/

# Roblox Item Sniper

A high-performance asynchronous Roblox Limited/UGC sniper written in Python. Monitors items and attempts to purchase them the instant they become collectible.

> [!CAUTION]
> **SECURITY WARNING:** This script requires your `.ROBLOSECURITY` cookie. **Never share your cookie or the `cookie.txt` file with anyone.** If someone gets your cookie, they have full access to your Roblox account.

## Features
- **High Speed**: Built with `aiohttp` and `asyncio` for low-latency monitoring.
- **In-Game Item Support**: Automatically detects and waits for the correct universe (game) required for specific items.
- **Autonomous Setup**: Can be configured via text files or interactive input.
- **Cross-Platform**: Supports Windows and Linux (with `uvloop` for enhanced performance).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-link>
   cd "Roblox Item Sniper"
   ```

2. **Set up a virtual environment (Recommended)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Roblox Cookie**: Create a file named `cookie.txt` in the root directory and paste your `.ROBLOSECURITY` cookie value there (just the value, starting with `_|WARNING:-DO-NOT-SHARE- ...`).
2. **Item Selection (Optional)**: 
   - Create a file named `item.txt` with the Item ID you want to snipe.
   - If this file is missing, the script will prompt you for the ID on startup.

## Usage

Run the sniper using:
```bash
python main.py
```

The script will:
1. Log in and display your username.
2. Poll the item status every ~60ms.
3. If the item is restricted to a specific game, it will tell you which `placeId` you need to join and wait for your presence to be detected in that game.
4. Purchase the item instantly once it becomes available.

## Disclaimer

This project is for educational purposes only. Automated purchasing (sniping) may be against the Roblox Terms of Service. Use at your own risk. The developer is not responsible for any account bans or loss of Robux.

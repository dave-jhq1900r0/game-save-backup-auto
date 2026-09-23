# game-save-backup-auto

I got tired of losing progress to corrupt saves or accidental choices in Stardew Valley and other games, so I wrote this background watcher. It monitors your game save directories, zips up changes when you save, and parses the save files to show your character stats and progress in the logs.

It runs entirely locally on Windows and uses a simple JSON config file to know what to watch.

## Installation

Clone the repository and install the dependencies:

```cmd
pip install -r requirements.txt
```

## Configuration

Create a `config.json` in the same directory as the script. It should define the games you want to track:

```json
{
  "backup_dir": "D:\\Backups\\Games",
  "targets": [
    {
      "name": "Stardew Valley",
      "watch_path": "%USERPROFILE%\\AppData\\Roaming\\StardewValley\\Saves",
      "game_type": "stardew_valley",
      "keep_backups": 10
    }
  ]
}
```

## Running

To start watching and backing up saves in the background:

```cmd
python backup.py --watch
```

Or trigger a single, manual scan and backup immediately:

```cmd
python backup.py --once
```

To view a quick summary of your parsed save stats:

```cmd
python backup.py --stats
```

<!-- checked: 2026-09-23 -->

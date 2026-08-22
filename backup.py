import argparse
import sys
import time
import zipfile
from pathlib import Path
from game_save_backup.parsers import get_save_stats

def getDirState(target_dir: Path) -> dict[Path, float]:
    """Returns a map of file paths to their last modified timestamps."""
    state = {}
    for p in target_dir.rglob("*"):
        if p.is_file():
            try:
                state[p] = p.stat().st_mtime
            except OSError:
                state[p] = 0.0
    return state

def create_backup(source_dir: Path, dest_dir: Path) -> Path:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    folder_name = source_dir.name
    zip_path = dest_dir / f"{folder_name}_{timestamp}.zip"
    
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    retries = 5
    for attempt in range(retries):
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in source_dir.rglob("*"):
                    if file_path.is_file():
                        zip_file.write(file_path, file_path.relative_to(source_dir))
            break
        except PermissionError:
            if attempt == retries - 1:
                raise
            time.sleep(0.5)
            
    return zip_path

def prune_old_backups(dest_dir: Path, prefix: str, keep_count: int):
    backups = sorted(
        [f for f in dest_dir.glob(f"{prefix}_*.zip") if f.is_file()],
        key=lambda x: x.name
    )
    if len(backups) > keep_count:
        to_delete = backups[:-keep_count]
        for f in to_delete:
            try:
                f.unlink()
            except OSError as e:
                print(f"Warning: Could not delete old backup {f.name}: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="Watch a game save folder and create zip backups on change."
    )
    parser.add_argument("source", type=str, help="Path to the game save directory to watch")
    parser.add_argument("backup_dir", type=str, help="Directory where backups will be saved")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds")
    parser.add_argument("--keep", type=int, default=15, help="Number of recent backups to keep")
    
    args = parser.parse_args()
    
    source_path = Path(args.source)
    backup_path = Path(args.backup_dir)
    
    if not source_path.is_dir():
        print(f"Error: Source directory '{source_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    print(f"Watching: {source_path}")
    print(f"Backups folder: {backup_path} (keeping last {args.keep})")
    
    last_state = getDirState(source_path)
    
    try:
        while True:
            time.sleep(args.interval)
            # TODO: handle the case where the source directory is temporarily inaccessible or deleted
            if not source_path.exists():
                continue
                
            current_state = getDirState(source_path)
            # print(f"DEBUG: current state files count: {len(current_state)}")
            if current_state != last_state:
                time.sleep(0.5)
                
                try:
                    zip_file = create_backup(source_path, backup_path)
                    print(f"[{time.strftime('%H:%M:%S')}] Save change detected! Backed up to {zip_file.name}")
                    
                    stats = get_save_stats(source_path)
                    if stats:
                        stat_line = ", ".join(f"{k}: {v}" for k, v in stats.items())
                        print(f"  Stats tracked -> {stat_line}")
                    
                    prune_old_backups(backup_path, source_path.name, args.keep)
                    last_state = getDirState(source_path)
                except PermissionError:
                    print("Warning: Files were locked by the game. Retrying in next cycle.", file=sys.stderr)
                    
    except KeyboardInterrupt:
        print("\nStopping backup watcher.")

if __name__ == "__main__":
    main()

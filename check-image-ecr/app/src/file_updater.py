import os
import shutil
from typing import List


def atomic_write(path: str, lines: List[str]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    # backup existing file
    if os.path.exists(path):
        backup_path = f"{path}.bak"
        shutil.copy2(path, backup_path)
    os.replace(tmp_path, path)
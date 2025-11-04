import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

import structlog


logger = structlog.get_logger()


@dataclass
class ConfigEntry:
    deployment: str
    image: str
    sha: str


class ConfigLoader:
    def __init__(self, path: str = "/app/config.txt"):
        self.path = path
        self._cache: Tuple[float, List[ConfigEntry]] = (0.0, [])

    def _parse_line(self, line: str, line_no: int) -> Optional[ConfigEntry]:
        line = line.strip()
        if not line or line.startswith("#"):
            return None

        first = line.find(":")
        last = line.rfind(":")
        if first == -1 or last == -1 or last == first:
            logger.warning("invalid_config_line", line_no=line_no, line=line)
            return None

        deployment = line[:first].strip()
        sha = line[last + 1 :].strip()
        image = line[first + 1 : last].strip()

        if not deployment or not image or not sha:
            logger.warning("empty_field_in_config", line_no=line_no, line=line)
            return None

        if not sha.startswith("sha256:"):
            logger.warning("invalid_sha_format", line_no=line_no, sha=sha)
            return None

        return ConfigEntry(deployment=deployment, image=image, sha=sha)

    def read(self) -> List[ConfigEntry]:
        try:
            stat = os.stat(self.path)
        except FileNotFoundError:
            logger.warning("config_file_missing", path=self.path)
            return []

        mtime = stat.st_mtime
        if mtime == self._cache[0] and self._cache[1]:
            return list(self._cache[1])

        entries: List[ConfigEntry] = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f, start=1):
                    entry = self._parse_line(line, i)
                    if entry:
                        entries.append(entry)
        except Exception as e:
            logger.error("read_config_error", error=str(e))
            return []

        self._cache = (mtime, entries)
        return list(entries)

    def format_lines(self, entries: List[ConfigEntry]) -> List[str]:
        return [f"{e.deployment}:{e.image}:{e.sha}\n" for e in entries]
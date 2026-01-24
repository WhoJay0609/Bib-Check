"""简单文件缓存"""

import json
import os
import time
import hashlib
import threading


class FileCache:
    """基于文件的简单缓存"""

    def __init__(self, config):
        self.enabled = bool(config.get('enabled', False))
        self.cache_dir = config.get('dir', '.cache/bib-check')
        self.ttl = int(config.get('ttl', 86400))
        self.max_size_mb = int(config.get('max_size_mb', 200))
        self._lock = threading.Lock()

        if self.enabled:
            os.makedirs(self.cache_dir, exist_ok=True)

    def get(self, key):
        if not self.enabled:
            return None
        path = self._key_to_path(key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            timestamp = data.get('ts', 0)
            if self.ttl > 0 and (time.time() - timestamp) > self.ttl:
                self._safe_remove(path)
                return None
            return data.get('value')
        except Exception:
            return None

    def set(self, key, value):
        if not self.enabled:
            return
        path = self._key_to_path(key)
        payload = {'ts': time.time(), 'value': value}
        with self._lock:
            try:
                os.makedirs(self.cache_dir, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(payload, f, ensure_ascii=False)
                self._prune_if_needed()
            except Exception:
                return

    def _key_to_path(self, key):
        digest = hashlib.sha256(key.encode('utf-8')).hexdigest()
        return os.path.join(self.cache_dir, f"{digest}.json")

    def _prune_if_needed(self):
        if self.max_size_mb <= 0:
            return
        total_size = 0
        entries = []
        for name in os.listdir(self.cache_dir):
            path = os.path.join(self.cache_dir, name)
            try:
                stat = os.stat(path)
            except FileNotFoundError:
                continue
            total_size += stat.st_size
            entries.append((stat.st_mtime, path, stat.st_size))

        max_bytes = self.max_size_mb * 1024 * 1024
        if total_size <= max_bytes:
            return

        entries.sort()
        for _, path, size in entries:
            self._safe_remove(path)
            total_size -= size
            if total_size <= max_bytes:
                break

    def _safe_remove(self, path):
        try:
            os.remove(path)
        except Exception:
            return

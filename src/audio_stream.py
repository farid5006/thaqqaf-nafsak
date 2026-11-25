"""موديول بث الملفات الصوتية الكبيرة تدريجياً مع دعم HTTP Range للتقديم والتأخير."""
import os
from typing import Any


def send_file_stream(handler: Any, fpath: str, ctype: str) -> None:
    """يبث الملف من القرص مباشرة دون تحميله بالذاكرة مع دعم طلبات النطاق (Range)."""
    size = os.path.getsize(fpath)
    rng = handler.headers.get("Range")
    start, end, status = 0, size - 1, 200
    if rng and rng.startswith("bytes="):
        parts = rng[6:].split(",")[0].split("-")
        if parts[0].strip().isdigit():
            start = int(parts[0].strip())
        if len(parts) > 1 and parts[1].strip().isdigit():
            end = min(int(parts[1].strip()), size - 1)
        if start >= size or start > end:
            handler.send_response(416)
            handler.send_header("Content-Range", f"bytes */{size}")
            handler.end_headers()
            return
        status = 206
    length = end - start + 1
    handler.send_response(status)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Accept-Ranges", "bytes")
    handler.send_header("Content-Length", str(length))
    if status == 206:
        handler.send_header("Content-Range", f"bytes {start}-{end}/{size}")
    handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()
    with open(fpath, "rb") as f:
        f.seek(start)
        rem = length
        while rem > 0:
            chunk = f.read(min(65536, rem))
            if not chunk:
                break
            try:
                handler.wfile.write(chunk)
            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                break
            rem -= len(chunk)

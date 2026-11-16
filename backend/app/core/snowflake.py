"""63 位有效雪花 ID 生成器（最高位 0 防负数；总位宽对标 Twitter Snowflake）。

布局（高位 → 低位）：
    0 [41 bits 时间戳 ms-自-EPOCH] [10 bits worker_id] [12 bits sequence]

- **EPOCH = 2025-01-01T00:00:00Z**（毫秒）→ 41 位可用 ~69 年到 2094 年
- **worker_id**：`SNOWFLAKE_WORKER_ID` 环境变量，0..1023；默认由 hostname+pid 派生
- **sequence**：同一 ms 内单 worker 可产生 4096 个，溢出 spin-wait 到下一 ms
- **时间回拨**：检测到 `now < _last_ms`（NTP 校时）→ spin-wait 至追上，不抛错

JS 精度：ID 量级 ≈ 2^45+~2^63，远超 JS `Number.MAX_SAFE_INTEGER (2^53-1)`。
后端 JSON 出口使用 `app.library.json.dumps_jssafe` 把超界 int 转 string。
"""
import os
import socket
import threading
import time
import zlib

EPOCH_MS = 1735689600000          # 2025-01-01T00:00:00Z UTC, ms
WORKER_BITS = 10                  # 0..1023
SEQ_BITS = 12                     # 0..4095 per ms per worker
WORKER_SHIFT = SEQ_BITS
TIME_SHIFT = WORKER_BITS + SEQ_BITS
MAX_SEQ = (1 << SEQ_BITS) - 1
MAX_WORKER = (1 << WORKER_BITS) - 1


class _Snowflake:
    def __init__(self, worker_id: int):
        if not 0 <= worker_id <= MAX_WORKER:
            raise ValueError(f"worker_id 必须在 [0, {MAX_WORKER}]，实际 {worker_id}")
        self.worker_id = worker_id
        self._last_ms = -1
        self._seq = 0
        self._lock = threading.Lock()

    def next_id(self) -> int:
        with self._lock:
            now = int(time.time() * 1000)
            # 时间回拨：spin 到追上上次时间，避免出现重复 ID
            if now < self._last_ms:
                while now < self._last_ms:
                    now = int(time.time() * 1000)
            if now == self._last_ms:
                self._seq = (self._seq + 1) & MAX_SEQ
                if self._seq == 0:
                    # 同 ms 4096 个序列用尽，等下一 ms
                    while now <= self._last_ms:
                        now = int(time.time() * 1000)
            else:
                self._seq = 0
            self._last_ms = now
            return ((now - EPOCH_MS) << TIME_SHIFT) | (self.worker_id << WORKER_SHIFT) | self._seq


def _resolve_worker_id() -> int:
    """worker_id 解析：显式 SNOWFLAKE_WORKER_ID 优先；否则按 hostname+pid 派生。

    多 worker / 多进程每进程一个 `_Snowflake` 实例。
    用 crc32(hostname:pid) & 1023 派生 worker_id 避免碰撞。
    """
    env = (os.environ.get("SNOWFLAKE_WORKER_ID") or "").strip()
    if env:
        return int(env) & MAX_WORKER
    seed = f"{socket.gethostname()}:{os.getpid()}".encode()
    return zlib.crc32(seed) & MAX_WORKER


_inst = _Snowflake(_resolve_worker_id())


def next_id() -> int:
    """生成下一个雪花 ID（线程安全）。"""
    return _inst.next_id()


def parse(snowflake_id: int) -> dict:
    """调试用：拆解 ID。返回 {ts_ms, worker, seq}。"""
    seq = snowflake_id & MAX_SEQ
    worker = (snowflake_id >> WORKER_SHIFT) & MAX_WORKER
    ts = (snowflake_id >> TIME_SHIFT) + EPOCH_MS
    return {"ts_ms": ts, "worker": worker, "seq": seq}


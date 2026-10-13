"""Approximate cross-platform process memory and CPU timing, without extra dependencies."""
from contextlib import contextmanager
from pathlib import Path
import ctypes
import os
import threading
import time

if os.name != "nt":
    import resource


def _windows_memory_mib():
    from ctypes import wintypes

    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)

    kernel32.GetCurrentProcess.argtypes = []
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE

    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

    handle = kernel32.GetCurrentProcess()

    counters = PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)

    ok = psapi.GetProcessMemoryInfo(
        handle,
        ctypes.byref(counters),
        counters.cb,
    )

    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())

    mib = 1024 * 1024

    return (
        counters.WorkingSetSize / mib,
        counters.PeakWorkingSetSize / mib,
    )


def rss_mib():
    if os.name == "nt":
        current, _ = _windows_memory_mib()
        return current

    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1]) / 1024

    raise RuntimeError("Linux process RSS is unavailable")


def high_water_mib():
    if os.name == "nt":
        _, peak = _windows_memory_mib()
        return peak

    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


@contextmanager
def measure_forward(device=None):
    cuda_enabled = (
        device is not None
        and getattr(device, "type", None) == "cuda"
    )

    if cuda_enabled:
        import torch
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)
        cuda_allocated_before = torch.cuda.memory_allocated(device)
        cuda_reserved_before = torch.cuda.memory_reserved(device)
    else:
        cuda_allocated_before = None
        cuda_reserved_before = None

    record = {
        "rss_before_mib": rss_mib(),
        "sampling_interval_s": 0.01,
        "process_high_water_before_mib": high_water_mib(),
    }

    if cuda_enabled:
        record["cuda_memory_allocated_before_mib"] = (
            cuda_allocated_before / 1024 / 1024
        )
        record["cuda_memory_reserved_before_mib"] = (
            cuda_reserved_before / 1024 / 1024
        )

    samples = [record["rss_before_mib"]]
    stop = threading.Event()

    def sample():
        while not stop.wait(record["sampling_interval_s"]):
            samples.append(rss_mib())

    monitor = threading.Thread(target=sample, daemon=True)
    monitor.start()

    wall = time.perf_counter()
    cpu = time.process_time()

    try:
        yield record
    finally:
        if cuda_enabled:
            torch.cuda.synchronize(device)

        record.update(
            wall_time_s=time.perf_counter() - wall,
            process_cpu_time_s=time.process_time() - cpu,
        )

        stop.set()
        monitor.join()

        record["rss_after_mib"] = rss_mib()
        record["sampled_peak_rss_mib"] = max(
            samples + [record["rss_after_mib"]]
        )
        record["process_high_water_after_mib"] = high_water_mib()

        if cuda_enabled:
            peak_allocated = torch.cuda.max_memory_allocated(device)
            peak_reserved = torch.cuda.max_memory_reserved(device)
            record["cuda_peak_memory_allocated_mib"] = peak_allocated / 1024 / 1024
            record["cuda_peak_memory_reserved_mib"] = peak_reserved / 1024 / 1024
            record["cuda_peak_memory_allocated_delta_mib"] = (
                peak_allocated - cuda_allocated_before
            ) / 1024 / 1024
            record["cuda_peak_memory_reserved_delta_mib"] = (
                peak_reserved - cuda_reserved_before
            ) / 1024 / 1024

        record["scope"] = (
            "model forward only; CPU process time includes all threads; "
            "RSS includes model and process; high-water values are cumulative; "
            "CUDA wall timing is synchronized and CUDA peak memory is recorded when applicable"
        )

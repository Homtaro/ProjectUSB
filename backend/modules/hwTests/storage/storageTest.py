import os
import shutil
import time
import hashlib
import random
import string
from pathlib import Path

# ==========================
# HELPERS
# ==========================

def get_drive_info(path):
    path = Path(path)
    if not path.exists():
        raise RuntimeError(f"Path {path} does not exist")

    #stat = os.statvfs(str(path))
    #total = stat.f_blocks * stat.f_frsize
    #free = stat.f_bavail * stat.f_frsize

    usage = shutil.disk_usage(str(path))
    total = usage.total
    free = usage.free

    fs_type = os.name  # placeholder, can use platform-specific methods if needed
    return {
        "path": str(path),
        "total_bytes": total,
        "free_bytes": free,
        "filesystem": fs_type,
    }


def random_bytes(size):
    return os.urandom(size)


def hash_file(file_path, chunk_size=1024*1024):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def measure_write(file_path, size_bytes):
    data = random_bytes(size_bytes)
    start = time.time()
    with open(file_path, "wb") as f:
        f.write(data)
    end = time.time()
    return end - start, data


def measure_read(file_path):
    start = time.time()
    with open(file_path, "rb") as f:
        data = f.read()
    end = time.time()
    return end - start, data


# ==========================
# TESTS
# ==========================

def single_file_test(target_path, size_mb=100):
    file_path = Path(target_path) / "test_single_file.bin"
    size_bytes = size_mb * 1024 * 1024

    print(f"\n[Single File Test] {size_mb} MB")
    write_time, data = measure_write(file_path, size_bytes)
    write_speed = size_bytes / write_time / 1024 / 1024

    read_time, read_data = measure_read(file_path)
    read_speed = size_bytes / read_time / 1024 / 1024

    file_hash = hashlib.sha256(data).hexdigest()
    read_hash = hashlib.sha256(read_data).hexdigest()
    integrity = file_hash == read_hash

    os.remove(file_path)

    return {
        "write_speed_MBps": round(write_speed, 2),
        "read_speed_MBps": round(read_speed, 2),
        "hash_match": integrity,
    }


def multi_file_test(target_path, num_files=10, size_mb=50):
    results = []
    print(f"\n[Multi-File Test] {num_files} files, {size_mb} MB each")

    for i in range(num_files):
        file_path = Path(target_path) / f"test_file_{i}.bin"
        size_bytes = size_mb * 1024 * 1024

        write_time, data = measure_write(file_path, size_bytes)
        write_speed = size_bytes / write_time / 1024 / 1024

        read_time, read_data = measure_read(file_path)
        read_speed = size_bytes / read_time / 1024 / 1024

        integrity = hashlib.sha256(data).hexdigest() == hashlib.sha256(read_data).hexdigest()

        results.append({
            "file": str(file_path.name),
            "write_MBps": round(write_speed, 2),
            "read_MBps": round(read_speed, 2),
            "hash_match": integrity,
        })

        os.remove(file_path)

    return results


# ==========================
# MAIN
# ==========================

if __name__ == "__main__":
    target = input("Enter path to test storage device (e.g., E:/): ").strip()
    info = get_drive_info(target)
    print("\n=== DEVICE INFO ===")
    for k, v in info.items():
        print(f"{k}: {v}")

    single_result = single_file_test(target, size_mb=100)
    print("\n=== SINGLE FILE TEST RESULT ===")
    for k, v in single_result.items():
        print(f"{k}: {v}")

    multi_result = multi_file_test(target, num_files=10, size_mb=50)
    print("\n=== MULTI-FILE TEST RESULTS ===")
    for r in multi_result:
        print(r)

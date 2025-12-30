import os
import time
import hashlib
import ctypes
import shutil

# ======================
# CONFIG
# ======================
SINGLE_FILE_SIZE_MB = 100
MULTI_FILE_COUNT = 10
MULTI_FILE_SIZE_MB = 50
SECTOR_SIZE = 512  # typical sector size, used for alignment
BUFFER_SIZE = 1024 * 1024  # 1 MB buffer for performance

# ======================
# WINDOWS UNBUFFERED I/O
# ======================
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_ALWAYS = 4
FILE_ATTRIBUTE_NORMAL = 0x80
FILE_FLAG_NO_BUFFERING = 0x20000000
FILE_FLAG_WRITE_THROUGH = 0x80000000

CreateFile = ctypes.windll.kernel32.CreateFileW
ReadFile = ctypes.windll.kernel32.ReadFile
WriteFile = ctypes.windll.kernel32.WriteFile
CloseHandle = ctypes.windll.kernel32.CloseHandle

def sector_aligned_buffer(size, sector_size=SECTOR_SIZE):
    buf = ctypes.create_string_buffer(size + sector_size)
    addr = ctypes.addressof(buf)
    offset = (sector_size - (addr % sector_size)) % sector_size
    return buf, offset

def write_file_unbuffered(path, size_mb):
    total_bytes = size_mb * 1024 * 1024
    buf, offset = sector_aligned_buffer(BUFFER_SIZE)
    hasher = hashlib.sha256()

    handle = CreateFile(
        path,
        GENERIC_WRITE,
        0,  # no sharing
        None,
        OPEN_ALWAYS,
        FILE_ATTRIBUTE_NORMAL | FILE_FLAG_NO_BUFFERING | FILE_FLAG_WRITE_THROUGH,
        None
    )
    if handle == -1:
        raise RuntimeError(f"CreateFile failed: {ctypes.GetLastError()}")

    start = time.time()
    bytes_written = 0
    while bytes_written < total_bytes:
        chunk_size = min(BUFFER_SIZE, total_bytes - bytes_written)
        # Random data generation
        data_chunk = os.urandom(chunk_size)
        hasher.update(data_chunk)
        ctypes.memmove(ctypes.addressof(buf) + offset, data_chunk, chunk_size)
        
        written = ctypes.c_ulong(0)
        if not WriteFile(handle, ctypes.byref(buf, offset), chunk_size, ctypes.byref(written), None):
            CloseHandle(handle)
            raise RuntimeError(f"WriteFile failed: {ctypes.GetLastError()}")
        bytes_written += written.value
        
    elapsed = time.time() - start
    CloseHandle(handle)
    return elapsed, hasher.hexdigest()

def read_file_unbuffered(path):
    total_bytes = os.path.getsize(path)
    buf, offset = sector_aligned_buffer(BUFFER_SIZE)
    hasher = hashlib.sha256()

    handle = CreateFile(
        path,
        GENERIC_READ,
        0,  # no sharing
        None,
        OPEN_ALWAYS,
        FILE_ATTRIBUTE_NORMAL | FILE_FLAG_NO_BUFFERING,
        None
    )
    if handle == -1:
        raise RuntimeError(f"CreateFile failed: {ctypes.GetLastError()}")

    start = time.time()
    bytes_read = 0
    while bytes_read < total_bytes:
        chunk_size = min(BUFFER_SIZE, total_bytes - bytes_read)
        read_bytes = ctypes.c_ulong(0)
        if not ReadFile(handle, ctypes.byref(buf, offset), chunk_size, ctypes.byref(read_bytes), None):
            CloseHandle(handle)
            raise RuntimeError(f"ReadFile failed: {ctypes.GetLastError()}")
        
        # Hash current chunk
        data = ctypes.string_at(ctypes.addressof(buf) + offset, read_bytes.value)
        hasher.update(data)
        bytes_read += read_bytes.value
        
    elapsed = time.time() - start
    CloseHandle(handle)
    return elapsed, hasher.hexdigest()

# ======================
# DEVICE INFO
# ======================
def get_device_info(path):
    usage = shutil.disk_usage(str(path))
    return {
        "path": path,
        "total_bytes": usage.total,
        "free_bytes": usage.free,
        "filesystem": "nt" if os.name == "nt" else "unknown"
    }

def single_file_test(path):
    file_path = os.path.join(path, "test_single_file.bin")
    size_mb = SINGLE_FILE_SIZE_MB
    print(f"\n[Single File Test] {size_mb} MB")
    
    write_time, write_hash = write_file_unbuffered(file_path, size_mb)
    read_time, read_hash = read_file_unbuffered(file_path)
    
    hash_match = write_hash == read_hash
    write_speed = size_mb / write_time
    read_speed = size_mb / read_time

    if os.path.exists(file_path):
        os.remove(file_path)

    return {
        "write_speed_MBps": round(write_speed, 2),
        "read_speed_MBps": round(read_speed, 2),
        "hash_match": hash_match
    }

def multi_file_test(path):
    size_mb = MULTI_FILE_SIZE_MB
    results = []
    print(f"\n[Multi-File Test] {MULTI_FILE_COUNT} files, {size_mb} MB each")
    
    for i in range(MULTI_FILE_COUNT):
        file_path = os.path.join(path, f"test_file_{i}.bin")
        write_time, write_hash = write_file_unbuffered(file_path, size_mb)
        read_time, read_hash = read_file_unbuffered(file_path)
        
        results.append({
            "file": os.path.basename(file_path),
            "write_MBps": round(size_mb / write_time, 2),
            "read_MBps": round(size_mb / read_time, 2),
            "hash_match": write_hash == read_hash
        })
        if os.path.exists(file_path):
            os.remove(file_path)

    return results

if __name__ == "__main__":
    target_path = input("Enter drive/folder path to test (e.g., D:\\): ").strip()
    try:
        info = get_device_info(target_path)
        print("\n=== DEVICE INFO ===")
        for k, v in info.items():
            print(f"{k}: {v}")

        single_result = single_file_test(target_path)
        print("\n=== SINGLE FILE TEST RESULT ===")
        for k, v in single_result.items():
            print(f"{k}: {v}")

        multi_results = multi_file_test(target_path)
        print("\n=== MULTI-FILE TEST RESULTS ===")
        for res in multi_results:
            print(res)
    except Exception as e:
        print(f"Error during test: {e}")

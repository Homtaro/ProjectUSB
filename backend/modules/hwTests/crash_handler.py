
import ctypes
from ctypes import wintypes
import sys

# Windows exception codes
EXCEPTION_ACCESS_VIOLATION = 0xC0000005
EXCEPTION_CONTINUE_SEARCH = 0
EXCEPTION_EXECUTE_HANDLER = 1

# Vectored Exception Handler
PVECTORED_EXCEPTION_HANDLER = ctypes.WINFUNCTYPE(
    wintypes.LONG,
    ctypes.POINTER(ctypes.c_void_p)
)


class EXCEPTION_RECORD(ctypes.Structure):
    pass


EXCEPTION_RECORD._fields_ = [
    ('ExceptionCode', wintypes.DWORD),
    ('ExceptionFlags', wintypes.DWORD),
    ('ExceptionRecord', ctypes.POINTER(EXCEPTION_RECORD)),
    ('ExceptionAddress', ctypes.c_void_p),
    ('NumberParameters', wintypes.DWORD),
    ('ExceptionInformation', ctypes.c_ulonglong * 15),
]


class EXCEPTION_POINTERS(ctypes.Structure):
    _fields_ = [
        ('ExceptionRecord', ctypes.POINTER(EXCEPTION_RECORD)),
        ('ContextRecord', ctypes.c_void_p),
    ]


_handler_installed = False
_handler_func = None


def exception_handler(exception_pointers):
    """Handle access violations during cleanup"""
    try:
        exc_record = exception_pointers.contents.ExceptionRecord.contents

        if exc_record.ExceptionCode == EXCEPTION_ACCESS_VIOLATION:
            print("Caught access violation during raw input cleanup - ignoring")
            # Return EXCEPTION_EXECUTE_HANDLER to suppress the crash
            return EXCEPTION_EXECUTE_HANDLER
    except Exception:
        pass

    # Let other exceptions through
    return EXCEPTION_CONTINUE_SEARCH


def install_exception_handler():
    """Install a vectored exception handler to catch access violations"""
    global _handler_installed, _handler_func

    if _handler_installed:
        return

    # Keep reference to prevent garbage collection
    _handler_func = PVECTORED_EXCEPTION_HANDLER(exception_handler)

    # Add vectored exception handler (first=1 means it runs first)
    result = ctypes.windll.kernel32.AddVectoredExceptionHandler(
        1,  # first
        _handler_func
    )

    if result:
        _handler_installed = True
        print("Installed exception handler for raw input cleanup")
    else:
        print("Warning: Failed to install exception handler")


def remove_exception_handler():
    """Remove the exception handler"""
    global _handler_installed, _handler_func

    if not _handler_installed or not _handler_func:
        return

    ctypes.windll.kernel32.RemoveVectoredExceptionHandler(_handler_func)
    _handler_installed = False
    _handler_func = None
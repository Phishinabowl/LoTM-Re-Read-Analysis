"""Windows 10+ job-contained creation, with explicit inherited diagnostic handles."""

import ctypes as ct
from ctypes import wintypes as wt
import os
import subprocess


class WindowsTree:
    def __init__(self, arguments, cwd, environment, stdout, stderr):
        import msvcrt

        self.api = ct.WinDLL("kernel32", use_last_error=True)
        self.job = self.process = None
        self.members = {}
        size = ct.c_size_t

        class Limits(ct.Structure):
            _fields_ = [
                ("user", ct.c_longlong),
                ("job_user", ct.c_longlong),
                ("flags", wt.DWORD),
                ("minimum", size),
                ("maximum", size),
                ("active", wt.DWORD),
                ("affinity", size),
                ("priority", wt.DWORD),
                ("scheduling", wt.DWORD),
            ]

        class Extended(ct.Structure):
            _fields_ = [
                ("basic", Limits),
                ("io", ct.c_ulonglong * 6),
                ("process_memory", size),
                ("job_memory", size),
                ("peak_process", size),
                ("peak_job", size),
            ]

        class Startup(ct.Structure):
            _fields_ = [
                ("cb", wt.DWORD),
                ("reserved", wt.LPWSTR),
                ("desktop", wt.LPWSTR),
                ("title", wt.LPWSTR),
                ("x", wt.DWORD),
                ("y", wt.DWORD),
                ("xsize", wt.DWORD),
                ("ysize", wt.DWORD),
                ("xchars", wt.DWORD),
                ("ychars", wt.DWORD),
                ("fill", wt.DWORD),
                ("flags", wt.DWORD),
                ("show", wt.WORD),
                ("reserved_size", wt.WORD),
                ("reserved_bytes", ct.POINTER(ct.c_byte)),
                ("stdin", wt.HANDLE),
                ("stdout", wt.HANDLE),
                ("stderr", wt.HANDLE),
            ]

        class StartupEx(ct.Structure):
            _fields_ = [("startup", Startup), ("attributes", ct.c_void_p)]

        class Information(ct.Structure):
            _fields_ = [("process", wt.HANDLE), ("thread", wt.HANDLE), ("pid", wt.DWORD), ("tid", wt.DWORD)]

        class Accounting(ct.Structure):
            _fields_ = [
                ("times", ct.c_longlong * 4),
                ("faults", wt.DWORD),
                ("total", wt.DWORD),
                ("active", wt.DWORD),
                ("terminated", wt.DWORD),
            ]

        self.Accounting = Accounting
        signatures = {
            "CreateJobObjectW": ([ct.c_void_p, wt.LPCWSTR], wt.HANDLE),
            "SetInformationJobObject": ([wt.HANDLE, ct.c_int, ct.c_void_p, wt.DWORD], wt.BOOL),
            "QueryInformationJobObject": ([wt.HANDLE, ct.c_int, ct.c_void_p, wt.DWORD, ct.c_void_p], wt.BOOL),
            "InitializeProcThreadAttributeList": ([ct.c_void_p, wt.DWORD, wt.DWORD, ct.POINTER(size)], wt.BOOL),
            "UpdateProcThreadAttribute": (
                [ct.c_void_p, wt.DWORD, size, ct.c_void_p, size, ct.c_void_p, ct.c_void_p],
                wt.BOOL,
            ),
            "DeleteProcThreadAttributeList": ([ct.c_void_p], None),
            "CreateProcessW": (
                [
                    wt.LPCWSTR,
                    wt.LPWSTR,
                    ct.c_void_p,
                    ct.c_void_p,
                    wt.BOOL,
                    wt.DWORD,
                    ct.c_void_p,
                    wt.LPCWSTR,
                    ct.c_void_p,
                    ct.POINTER(Information),
                ],
                wt.BOOL,
            ),
            "CloseHandle": ([wt.HANDLE], wt.BOOL),
            "GetExitCodeProcess": ([wt.HANDLE, ct.POINTER(wt.DWORD)], wt.BOOL),
            "WaitForSingleObject": ([wt.HANDLE, wt.DWORD], wt.DWORD),
            "TerminateJobObject": ([wt.HANDLE, wt.UINT], wt.BOOL),
            "OpenProcess": ([wt.DWORD, wt.BOOL, wt.DWORD], wt.HANDLE),
            "IsProcessInJob": ([wt.HANDLE, wt.HANDLE, ct.POINTER(wt.BOOL)], wt.BOOL),
        }
        for name, (parameters, result) in signatures.items():
            function = getattr(self.api, name)
            function.argtypes, function.restype = parameters, result
        attributes = None
        initialized = False
        handles = []
        try:
            self.job = self.api.CreateJobObjectW(None, None)
            self.check(self.job)
            limits = Extended()
            limits.basic.flags = 0x2000  # KILL_ON_JOB_CLOSE; no breakaway permission.
            self.check(self.api.SetInformationJobObject(self.job, 9, ct.byref(limits), ct.sizeof(limits)))
            required = size()
            self.api.InitializeProcThreadAttributeList(None, 2, 0, ct.byref(required))
            attributes = ct.create_string_buffer(required.value)
            self.check(self.api.InitializeProcThreadAttributeList(attributes, 2, 0, ct.byref(required)))
            initialized = True
            with open(os.devnull, "rb") as stdin:
                handles = [msvcrt.get_osfhandle(file.fileno()) for file in (stdin, stdout, stderr)]
                for handle in handles:
                    os.set_handle_inheritable(handle, True)
                inherit = (wt.HANDLE * 3)(*handles)
                jobs = (wt.HANDLE * 1)(self.job)
                self.check(
                    self.api.UpdateProcThreadAttribute(attributes, 0, 0x20002, inherit, ct.sizeof(inherit), None, None)
                )
                self.check(
                    self.api.UpdateProcThreadAttribute(attributes, 0, 0x2000D, jobs, ct.sizeof(jobs), None, None)
                )
                startup = StartupEx()
                startup.startup.cb = ct.sizeof(startup)
                startup.startup.flags = 0x100  # STARTF_USESTDHANDLES
                startup.startup.stdin, startup.startup.stdout, startup.startup.stderr = handles
                startup.attributes = ct.cast(attributes, ct.c_void_p)
                information = Information()
                command = ct.create_unicode_buffer(subprocess.list2cmdline(arguments))
                block = ct.create_unicode_buffer(
                    "\0".join(
                        f"{key}={value}" for key, value in sorted(environment.items(), key=lambda row: row[0].upper())
                    )
                    + "\0\0"
                )
                # Atomic JOB_LIST assignment avoids a create/assign race, even if the guardian dies.
                self.check(
                    self.api.CreateProcessW(
                        arguments[0],
                        command,
                        None,
                        None,
                        True,
                        0x80000 | 0x400 | 0x8000000,
                        block,
                        str(cwd),
                        ct.byref(startup),
                        ct.byref(information),
                    )
                )
                self.process, self.pid = information.process, information.pid
                self.check(self.api.CloseHandle(information.thread))
        except BaseException:
            self.close()
            raise
        finally:
            for handle in handles:
                try:
                    os.set_handle_inheritable(handle, False)
                except OSError:
                    pass  # stdin may already be closed; stdout/stderr stay private.
            if initialized:
                self.api.DeleteProcThreadAttributeList(attributes)

    @staticmethod
    def check(value):
        if not value:
            raise ct.WinError(ct.get_last_error())
        return value

    def poll(self):
        wait = self.api.WaitForSingleObject(self.process, 0)
        if wait == 258:
            return None
        if wait != 0:
            raise ct.WinError(ct.get_last_error())
        result = wt.DWORD()
        self.check(self.api.GetExitCodeProcess(self.process, ct.byref(result)))
        return result.value

    def active(self):
        capacity = 64
        while True:
            data = ct.create_string_buffer(8 + ct.sizeof(ct.c_size_t) * capacity)
            if self.api.QueryInformationJobObject(self.job, 3, data, len(data), None):
                break
            if ct.get_last_error() != 234 or capacity >= 65536:
                raise ct.WinError(ct.get_last_error())
            capacity *= 2
        count = wt.DWORD.from_buffer(data, 4).value
        identifiers = (ct.c_size_t * count).from_buffer(data, 8)
        for pid in identifiers:
            if pid in self.members:
                continue
            handle = self.api.OpenProcess(0x100000 | 0x1000, False, pid)
            if not handle:
                if ct.get_last_error() == 87:  # Already exited before OpenProcess.
                    continue
                raise ct.WinError(ct.get_last_error())
            belongs = wt.BOOL()
            try:
                self.check(self.api.IsProcessInJob(handle, self.job, ct.byref(belongs)))
                if belongs.value:
                    self.members[pid] = handle
                    handle = None
            finally:
                if handle:
                    self.check(self.api.CloseHandle(handle))
        record = self.Accounting()
        self.check(self.api.QueryInformationJobObject(self.job, 1, ct.byref(record), ct.sizeof(record), None))
        live = record.active > 0
        for handle in self.members.values():
            wait = self.api.WaitForSingleObject(handle, 0)
            if wait not in (0, 258):
                raise ct.WinError(ct.get_last_error())
            live = live or wait == 258
        return live or self.poll() is None

    def graceful(self):
        return "unsupported-no-shared-console"

    def force(self):
        self.check(self.api.TerminateJobObject(self.job, 1))

    def close(self):
        for name in ("job", "process"):
            handle = getattr(self, name, None)
            if handle:
                self.check(self.api.CloseHandle(handle))
                setattr(self, name, None)
        for handle in self.members.values():
            self.check(self.api.CloseHandle(handle))
        self.members.clear()

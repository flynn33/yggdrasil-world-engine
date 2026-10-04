"""Explicit Windows host assembly for reference Diagnostics [YWE-REQ-0042].

This is a development reference adapter. Protected NTFS files provide the
declared ordinary-other-principal confidentiality boundary; they do not promise
encryption, power-loss durability, or protection from the same user/admin/SYSTEM.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import threading
import time
import uuid

from core.ash_pattern_engine import diagnostics_values as dv
from core.ash_pattern_engine import state_values as sv


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


class WindowsDiagnosticsClock:
    """Actual host observations; no caller-selected timestamp or zero fallback."""
    def read(self):
        utc = monotonic = None
        try:
            utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        except (OSError, OverflowError, ValueError):
            pass
        try:
            observed = time.monotonic_ns()
            if type(observed) is int and 0 <= observed <= (1 << 64) - 1:
                monotonic = observed
        except (OSError, OverflowError, ValueError):
            pass
        return dv.ClockObservation(utc, monotonic,
                                   None if utc is not None else "CLOCK_UNAVAILABLE",
                                   None if monotonic is not None else "CLOCK_UNAVAILABLE")


class _SecurityAttributes(ctypes.Structure):
    _fields_ = [("length", w.DWORD), ("descriptor", w.LPVOID), ("inherit", w.BOOL)]


class _FileInformation(ctypes.Structure):
    _fields_ = [("attributes", w.DWORD), ("creation", w.FILETIME),
               ("access", w.FILETIME), ("write", w.FILETIME),
               ("volume", w.DWORD), ("size_high", w.DWORD), ("size_low", w.DWORD),
               ("links", w.DWORD), ("index_high", w.DWORD), ("index_low", w.DWORD)]


class _AclSize(ctypes.Structure):
    _fields_ = [("count", w.DWORD), ("used", w.DWORD), ("free", w.DWORD)]


class _AceHeader(ctypes.Structure):
    _fields_ = [("kind", ctypes.c_ubyte), ("flags", ctypes.c_ubyte), ("size", w.WORD)]


class _WinSecurity:
    def __init__(self):
        if os.name != "nt":
            raise dv.DiagnosticsContractError("STORAGE_PROTECTION_UNAVAILABLE", "STORE")
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        self.a = ctypes.WinDLL("advapi32", use_last_error=True)
        declarations = (
            (self.k, "GetCurrentProcess", [], w.HANDLE),
            (self.k, "CloseHandle", [w.HANDLE], w.BOOL),
            (self.k, "LocalFree", [w.LPVOID], w.LPVOID),
            (self.k, "CreateDirectoryW", [w.LPCWSTR, ctypes.POINTER(_SecurityAttributes)], w.BOOL),
            (self.k, "CreateFileW", [w.LPCWSTR, w.DWORD, w.DWORD,
              ctypes.POINTER(_SecurityAttributes), w.DWORD, w.DWORD, w.HANDLE], w.HANDLE),
            (self.k, "GetFileInformationByHandle", [w.HANDLE, ctypes.POINTER(_FileInformation)], w.BOOL),
            (self.k, "GetVolumeInformationW", [w.LPCWSTR, w.LPWSTR, w.DWORD,
              ctypes.POINTER(w.DWORD), ctypes.POINTER(w.DWORD), ctypes.POINTER(w.DWORD), w.LPWSTR, w.DWORD], w.BOOL),
            (self.a, "OpenProcessToken", [w.HANDLE, w.DWORD, ctypes.POINTER(w.HANDLE)], w.BOOL),
            (self.a, "GetTokenInformation", [w.HANDLE, w.DWORD, w.LPVOID, w.DWORD, ctypes.POINTER(w.DWORD)], w.BOOL),
            (self.a, "ConvertSidToStringSidW", [w.LPVOID, ctypes.POINTER(w.LPWSTR)], w.BOOL),
            (self.a, "ConvertStringSecurityDescriptorToSecurityDescriptorW", [w.LPCWSTR, w.DWORD, ctypes.POINTER(w.LPVOID), ctypes.POINTER(w.ULONG)], w.BOOL),
            (self.a, "GetSecurityInfo", [w.HANDLE, w.DWORD, w.DWORD,
              ctypes.POINTER(w.LPVOID), ctypes.POINTER(w.LPVOID), ctypes.POINTER(w.LPVOID), ctypes.POINTER(w.LPVOID), ctypes.POINTER(w.LPVOID)], w.DWORD),
            (self.a, "GetSecurityDescriptorControl", [w.LPVOID, ctypes.POINTER(w.WORD), ctypes.POINTER(w.DWORD)], w.BOOL),
            (self.a, "GetAclInformation", [w.LPVOID, w.LPVOID, w.DWORD, w.DWORD], w.BOOL),
            (self.a, "GetAce", [w.LPVOID, w.DWORD, ctypes.POINTER(w.LPVOID)], w.BOOL),
        )
        for dll, name, args, result in declarations:
            function = getattr(dll, name)
            function.argtypes, function.restype = args, result
        token, size = w.HANDLE(), w.DWORD()
        self.check(self.a.OpenProcessToken(self.k.GetCurrentProcess(), 8, ctypes.byref(token)))
        try:
            self.a.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))
            buffer = ctypes.create_string_buffer(size.value)
            self.check(self.a.GetTokenInformation(token, 1, buffer, size, ctypes.byref(size)))
            self.sid = self.sid_text(ctypes.cast(buffer, ctypes.POINTER(w.LPVOID))[0])
        finally:
            self.k.CloseHandle(token)
        self.descriptor = w.LPVOID()
        sddl = f"O:{self.sid}D:P(A;OICI;FA;;;{self.sid})(A;OICI;FA;;;SY)"
        self.check(self.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            sddl, 1, ctypes.byref(self.descriptor), None))
        self.attributes = _SecurityAttributes(ctypes.sizeof(_SecurityAttributes), self.descriptor, False)

    @staticmethod
    def check(value):
        if not value:
            raise OSError(ctypes.get_last_error())

    def sid_text(self, pointer):
        text = w.LPWSTR()
        self.check(self.a.ConvertSidToStringSidW(pointer, ctypes.byref(text)))
        try:
            return text.value
        finally:
            self.k.LocalFree(ctypes.cast(text, w.LPVOID))

    def open_directory(self, path):
        handle = self.k.CreateFileW(str(path), 0x20080, 3, None, 3, 0x02200000, None)
        if handle == ctypes.c_void_p(-1).value:
            raise OSError(ctypes.get_last_error())
        return handle

    def identity(self, handle, *, directory):
        info = _FileInformation()
        self.check(self.k.GetFileInformationByHandle(handle, ctypes.byref(info)))
        if info.attributes & 0x400 or bool(info.attributes & 0x10) != directory:
            raise dv.DiagnosticsContractError("STORAGE_REPARSE_REFUSED", "STORE")
        return (info.volume, (info.index_high << 32) | info.index_low)

    def security(self, handle, *, private):
        owner, acl, descriptor = w.LPVOID(), w.LPVOID(), w.LPVOID()
        error = self.a.GetSecurityInfo(handle, 1, 5, ctypes.byref(owner), None,
                                       ctypes.byref(acl), None, ctypes.byref(descriptor))
        if error:
            raise OSError(error)
        try:
            control, revision, size = w.WORD(), w.DWORD(), _AclSize()
            self.check(self.a.GetSecurityDescriptorControl(descriptor, ctypes.byref(control), ctypes.byref(revision)))
            if not acl or not control.value & 4:
                raise dv.DiagnosticsContractError("STORAGE_PROTECTION_UNAVAILABLE", "STORE")
            self.check(self.a.GetAclInformation(acl, ctypes.byref(size), ctypes.sizeof(size), 2))
            grants = []
            for i in range(size.count):
                pointer = w.LPVOID()
                self.check(self.a.GetAce(acl, i, ctypes.byref(pointer)))
                header = ctypes.cast(pointer, ctypes.POINTER(_AceHeader)).contents
                if header.flags & 8:  # inherit-only does not authorize parent modification
                    continue
                if header.kind != 0:
                    if header.kind != 1:  # unfamiliar callback/object ACE: fail closed
                        raise dv.DiagnosticsContractError("STORAGE_PARENT_UNTRUSTED", "STORE")
                    continue
                mask = ctypes.c_uint32.from_address(pointer.value + 4).value
                principal = self.sid_text(pointer.value + 8)
                grants.append((principal, mask))
            if private:
                if self.sid_text(owner) != self.sid or not control.value & 0x1000:
                    raise dv.DiagnosticsContractError("STORAGE_PROTECTION_UNAVAILABLE", "STORE")
                if len(grants) != 2 or {sid for sid, _ in grants} != {self.sid, "S-1-5-18"}:
                    raise dv.DiagnosticsContractError("STORAGE_PROTECTION_UNAVAILABLE", "STORE")
                if any(mask != 0x1f01ff for _, mask in grants):
                    raise dv.DiagnosticsContractError("STORAGE_PROTECTION_UNAVAILABLE", "STORE")
            else:
                trusted = {self.sid, "S-1-5-18", "S-1-5-32-544"}
                if any(sid not in trusted and mask & (0xc0040 | 0x10000000)
                       for sid, mask in grants):
                    raise dv.DiagnosticsContractError("STORAGE_PARENT_UNTRUSTED", "STORE")
            return True
        finally:
            self.k.LocalFree(descriptor)

    def close(self):
        if self.descriptor:
            self.k.LocalFree(self.descriptor)
            self.descriptor = None


class WindowsProtectedStore:
    """Fresh direct volume-root store; every content file has its own private DACL."""
    def __init__(self, parent=Path("D:/")):
        parent = Path(parent)
        if parent != Path(parent.anchor) or not parent.is_absolute() or not re.fullmatch(r"[A-Za-z]:\\", str(parent)):
            raise dv.DiagnosticsContractError("STORAGE_PARENT_UNTRUSTED", "STORE")
        self._native, self._lock = _WinSecurity(), threading.RLock()
        self._parent, self._files, self._pair = parent, {}, None
        self._unconfirmed_files = {}
        self._parent_handle = self._root_handle = None
        self._closed = False
        try:
            self._parent_handle = self._native.open_directory(parent)
            self._parent_identity = self._native.identity(self._parent_handle, directory=True)
            self._native.security(self._parent_handle, private=False)
            flags, volume, maximum = w.DWORD(), w.DWORD(), w.DWORD()
            self._native.check(self._native.k.GetVolumeInformationW(str(parent), None, 0,
                ctypes.byref(volume), ctypes.byref(maximum), ctypes.byref(flags), None, 0))
            if not flags.value & 8:
                raise dv.DiagnosticsContractError("STORAGE_PROTECTION_UNAVAILABLE", "STORE")
            self.root = parent / ("ywe-reference-diagnostics-" + uuid.uuid4().hex)
            self._native.check(self._native.k.CreateDirectoryW(str(self.root), ctypes.byref(self._native.attributes)))
            self._root_handle = self._native.open_directory(self.root)
            self._root_identity = self._native.identity(self._root_handle, directory=True)
            self._native.security(self._root_handle, private=True)
        except BaseException:
            self.close()
            raise

    def verify(self):
        try:
            with self._lock:
                for path, held, expected, private in ((self._parent, self._parent_handle, self._parent_identity, False),
                                                    (self.root, self._root_handle, self._root_identity, True)):
                    if self._native.identity(held, directory=True) != expected:
                        raise dv.DiagnosticsContractError("STORAGE_IDENTITY_CHANGED", "STORE")
                    self._native.security(held, private=private)
                    reopened = self._native.open_directory(path)
                    try:
                        if self._native.identity(reopened, directory=True) != expected:
                            raise dv.DiagnosticsContractError("STORAGE_IDENTITY_CHANGED", "STORE")
                    finally:
                        self._native.k.CloseHandle(reopened)
                return dv.StorageVerification("VERIFIED", True, True, True,
                    ("EFFECTIVE_USER", "SYSTEM"), True, True, True, None)
        except dv.DiagnosticsContractError as error:
            return dv.StorageVerification("UNAVAILABLE", False, False, False,
                ("EFFECTIVE_USER", "SYSTEM"), False, False, False, error.code)
        except OSError:
            return dv.StorageVerification("UNAVAILABLE", False, False, False,
                ("EFFECTIVE_USER", "SYSTEM"), False, False, False, "STORAGE_PROTECTION_UNAVAILABLE")

    def _write(self, name, payload, *, cap, replace=False):
        if type(payload) is not bytes or not 1 <= len(payload) <= cap:
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_REJECTED", "STORE")
        if self.verify().status != "VERIFIED":
            raise dv.DiagnosticsContractError("STORAGE_IDENTITY_CHANGED", "STORE")
        occupied = sum(size for size, _ in self._files.values()) + sum(
            size for name, size in self._unconfirmed_files.items() if name not in self._files)
        if occupied + len(payload) > 134217728:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_BYTE_LIMIT", "STORE")
        path = self.root / name
        if replace and name in self._files:
            self._check_file(name)
            path.unlink()
            del self._files[name]
        handle = self._native.k.CreateFileW(str(path), 0xc0020080, 0,
            ctypes.byref(self._native.attributes), 1, 0x00200080, None)
        if handle == ctypes.c_void_p(-1).value:
            code = "STORAGE_PATH_ALREADY_EXISTS" if ctypes.get_last_error() in (80, 183) else "STORAGE_COMMIT_REJECTED"
            raise dv.DiagnosticsContractError(code, "STORE")
        import msvcrt
        # Atomic creation can succeed before a later write/verification fails.
        # Reserve its bounded possible bytes and keep that name unavailable;
        # an unconfirmed file is never silently adopted or reported purged.
        self._unconfirmed_files[name] = len(payload)
        try:
            before = self._native.identity(handle, directory=False)
            self._native.security(handle, private=True)
            fd = msvcrt.open_osfhandle(handle, os.O_RDWR | os.O_BINARY)
        except BaseException:
            self._native.k.CloseHandle(handle)
            raise
        with os.fdopen(fd, "w+b") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
            output.seek(0)
            if output.read() != payload or self._native.identity(handle, directory=False) != before:
                raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED", "STORE")
            self._native.security(handle, private=True)
        self._files[name] = (len(payload), before)
        if self.verify().status != "VERIFIED":
            raise dv.DiagnosticsContractError("STORAGE_IDENTITY_CHANGED", "STORE")
        del self._unconfirmed_files[name]

    def _check_file(self, name):
        handle = self._native.k.CreateFileW(str(self.root / name), 0x20080, 3, None, 3, 0x00200080, None)
        if handle == ctypes.c_void_p(-1).value:
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_UNCONFIRMED", "STORE")
        try:
            if self._native.identity(handle, directory=False) != self._files[name][1]:
                raise dv.DiagnosticsContractError("STORAGE_IDENTITY_CHANGED", "STORE")
            self._native.security(handle, private=True)
        finally:
            self._native.k.CloseHandle(handle)

    def _commit(self, sequence, name, payload, cap, *, replace=False):
        with self._lock:
            try:
                if sequence is not None and (type(sequence) is not int or not 0 <= sequence < 1 << 64):
                    raise dv.DiagnosticsContractError("STORAGE_COMMIT_REJECTED", "STORE")
                self._write(name, payload, cap=cap, replace=replace)
                return dv.StorageReceipt(sequence, "COMMITTED", None)
            except dv.DiagnosticsContractError as error:
                return dv.StorageReceipt(sequence, "REJECTED", error.code)
            except OSError:
                return dv.StorageReceipt(sequence, "UNKNOWN", "STORAGE_COMMIT_UNCONFIRMED")

    def commit_event(self, sequence, redacted_bytes):
        return self._commit(sequence, f"event-{sequence:020d}.json", redacted_bytes, 32768)

    def commit_supporting(self, sequence, kind, evidence_alias, redacted_bytes):
        if kind not in dv.enum_values("SupportingKind") or type(evidence_alias) is not str or not re.fullmatch(r"ref:[0-9]{6}", evidence_alias):
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_REJECTED", "STORE")
        return self._commit(sequence, f"support-{kind}-{evidence_alias[4:]}.json", redacted_bytes, 32768)

    def commit_meta(self, sequence, redacted_bytes):
        return self._commit(sequence, f"meta-{sequence:020d}.json", redacted_bytes, 3072)

    def commit_incident(self, sequence, incident_alias, redacted_bytes):
        if type(incident_alias) is not str or not re.fullmatch(r"ref:[0-9]{6}", incident_alias):
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_REJECTED", "STORE")
        return self._commit(sequence, f"incident-{sequence:020d}-{incident_alias[4:]}.json", redacted_bytes, 32768)

    def commit_health(self, sequence, redacted_bytes):
        return self._commit(sequence, "health.json", redacted_bytes, 8192, replace=True)

    def commit_fallback_health(self, sequence, redacted_bytes):
        return self._commit(sequence, "fallback-health.json", redacted_bytes, 8192, replace=True)

    def write_pair(self, bundle_alias, json_bytes, markdown_bytes, manifest_bytes, *, last_included_sequence):
        if type(bundle_alias) is not str or not re.fullmatch(r"ref:[0-9]{6}", bundle_alias):
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_REJECTED", "STORE")
        parts = []
        names = (("JSON", "diagnostics.json", json_bytes, 33554432),
                 ("MARKDOWN", "diagnostics.md", markdown_bytes, 50331648),
                 ("MANIFEST", "manifest.json", manifest_bytes, 65536))
        with self._lock:
            failure, failed_part = None, "JSON"
            if self._pair is not None:
                failure = "EXPORT_SLOT_OCCUPIED"
            else:
                self._pair = bundle_alias
            for kind, name, payload, cap in names:
                if failure is None:
                    try:
                        self._write(name, payload, cap=cap)
                        parts.append(dv.PartReceipt(kind, name, "CONFIRMED", len(payload), hashlib.sha256(payload).hexdigest(), None))
                        continue
                    except dv.DiagnosticsContractError as error:
                        failure = error.code
                    except OSError:
                        failure = "STORAGE_COMMIT_UNCONFIRMED"
                    failed_part = kind
                    parts.append(dv.PartReceipt(kind, name, "WRITTEN_UNCONFIRMED", None, None, failure))
                else:
                    parts.append(dv.PartReceipt(kind, name, "NOT_WRITTEN", None, None, None))
            if failure:
                return dv.StorePairFailure(bundle_alias, tuple(parts), last_included_sequence, failed_part, failure)
            return dv.StorePairReceipt(bundle_alias, tuple(parts), last_included_sequence)

    def purge_bundle(self, bundle_alias):
        with self._lock:
            if bundle_alias != self._pair:
                return dv.StorePurgeReceipt(bundle_alias, "REJECTED", 0, 0, "DIAGNOSTICS_RECORD_NONCONFORMANT")
            if any(name in self._unconfirmed_files for name in ("diagnostics.json", "diagnostics.md", "manifest.json")):
                return dv.StorePurgeReceipt(bundle_alias, "REJECTED", 0, 0, "STORAGE_COMMIT_UNCONFIRMED")
            removed = size = 0
            try:
                if self.verify().status != "VERIFIED":
                    raise dv.DiagnosticsContractError("STORAGE_IDENTITY_CHANGED", "STORE")
                for name in ("diagnostics.json", "diagnostics.md", "manifest.json"):
                    if name in self._files:
                        self._check_file(name)
                        size += self._files[name][0]
                        (self.root / name).unlink()
                        del self._files[name]
                        removed += 1
                self._pair = None
                return dv.StorePurgeReceipt(bundle_alias, "COMPLETED", removed, size, None)
            except (OSError, dv.DiagnosticsContractError):
                return dv.StorePurgeReceipt(bundle_alias, "REJECTED", removed, size, "STORAGE_COMMIT_UNCONFIRMED")

    def purge_capture(self, request):
        if type(request) is not dv.CapturePurgeRequest:
            raise dv.DiagnosticsContractError("STORAGE_COMMIT_REJECTED", "STORE")
        keys = tuple(dv.CaptureObjectKey("EVENT", sequence, None, None) for sequence in request.event_sequences) or request.supporting_keys
        observations = []
        with self._lock:
            for key in keys:
                name = (f"event-{key.sequence:020d}.json" if key.kind == "EVENT" else
                        f"support-{key.supporting_kind}-{key.evidence_reference[4:]}.json")
                try:
                    if name in self._unconfirmed_files:
                        observations.append(dv.CaptureRemovalObservation(key, "UNCONFIRMED", None, "STORAGE_COMMIT_UNCONFIRMED"))
                        continue
                    if name not in self._files:
                        observations.append(dv.CaptureRemovalObservation(key, "NOT_REMOVED", 0, "STORAGE_COMMIT_REJECTED"))
                        continue
                    if self.verify().status != "VERIFIED":
                        raise dv.DiagnosticsContractError("STORAGE_IDENTITY_CHANGED", "STORE")
                    self._check_file(name)
                    size = self._files[name][0]
                    (self.root / name).unlink()
                    if (self.root / name).exists() or self.verify().status != "VERIFIED":
                        raise dv.DiagnosticsContractError("STORAGE_IDENTITY_CHANGED", "STORE")
                    del self._files[name]
                    observations.append(dv.CaptureRemovalObservation(key, "REMOVED", size, None))
                except (OSError, dv.DiagnosticsContractError):
                    observations.append(dv.CaptureRemovalObservation(key, "UNCONFIRMED", None, "STORAGE_COMMIT_UNCONFIRMED"))
            removed = sum(row.status == "REMOVED" for row in observations)
            status = "COMPLETED" if removed == len(observations) else "PARTIAL" if removed else "REJECTED"
            return dv.StoreCapturePurgeReceipt(status, tuple(observations), None if status == "COMPLETED" else "STORAGE_COMMIT_UNCONFIRMED")

    def close(self):
        if not self._closed:
            if self._root_handle is not None:
                self._native.k.CloseHandle(self._root_handle)
            if self._parent_handle is not None:
                self._native.k.CloseHandle(self._parent_handle)
            self._native.close()
            self._closed = True


def assemble_reference_diagnostics(root: Path, *, release=False, parent=Path("D:/")):
    """Verify selected checkout/source bytes and assemble actual configured owners."""
    from core.ash_pattern_engine import diagnostics
    root = Path(root).resolve()
    if Path(sv.__file__).resolve() != root / "core/ash_pattern_engine/state_values.py":
        raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
    if (root / "VERSION").read_text(encoding="utf-8-sig").strip() != "2.0.23":
        raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
    truth = json.loads((root / "data/governance/repository_truth_manifest.json").read_text(encoding="utf-8-sig"))
    if truth.get("repository_baseline", {}).get("value") != "2.0.23":
        raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
    manifest = json.loads((root / "data/governance/ash_dependency_identity.json").read_text(encoding="utf-8-sig"))
    normalized = lambda p: p.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    rows = []
    for entry in manifest["files"]:
        relative = entry["relative_path"]
        actual = hashlib.sha256(normalized(root / manifest["canonical_source_root"] / relative)).hexdigest()
        if actual != entry["sha256"]:
            raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
        rows.append((relative, actual))
    aggregate = hashlib.sha256("".join(p + "\0" + digest + "\n" for p, digest in sorted(rows)).encode("utf-8")).hexdigest()
    if aggregate != dict(sv.CANONICAL_BINDING_FIELDS)["aggregate_sha256"]:
        raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
    policy = root / "docs/architecture/m3_recovery_safety_policy.md"
    if hashlib.sha256(normalized(policy)).hexdigest() != dv.SafeRecoverySafetyPolicy.policy_sha256:
        raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, check=True, capture_output=True, text=True).stdout.splitlines()
    if len(dirty) > 128:
        raise dv.DiagnosticsContractError("DIAGNOSTICS_CONFIG_INVALID", "ORIGINAL_SOURCE")
    provenance = dv.SourceProvenance("VERIFIED_DIRTY" if dirty else "VERIFIED_CLEAN", revision,
        tuple(f"ref:{i + 4:06d}" for i in range(len(dirty))), None)
    implementation = "REFERENCE_RELEASE_DIAGNOSTICS" if release else "REFERENCE_DEVELOPMENT_DIAGNOSTICS"
    profile_id = "REFERENCE_RELEASE" if release else "REFERENCE_DEVELOPMENT"
    architecture = {"AMD64": "X86_64", "x86_64": "X86_64", "ARM64": "ARM64", "aarch64": "ARM64"}.get(platform.machine(), "UNKNOWN")
    unavailable = () if architecture != "UNKNOWN" else (dv.MissingCoverage("ARCHITECTURE", "UNAVAILABLE", "NOT_MEASURED"),)
    environment = dv.DiagnosticsEnvironment("WINDOWS", tuple(sys.version_info[:3]), architecture, "HOST", unavailable)
    identity = dv.DiagnosticsIdentity("2.0.23", implementation, profile_id, "ref:000001", revision, provenance, "ref:000002", environment)
    profile = dv.DiagnosticsProfile(profile_id, implementation, "ref:000003", not release)
    store = WindowsProtectedStore(parent)
    try:
        owner = diagnostics.ReferenceReleaseDiagnostics if release else diagnostics.ReferenceDevelopmentDiagnostics
        return owner(identity, profile, store, WindowsDiagnosticsClock())
    except BaseException:
        store.close()
        raise

"""Bounded M4 commit/replay reference oracle, not a production storage adapter.

Contract: docs/architecture/m4_commit_journal_contract.md [YWE-REQ-0052].
Domain reducers are trusted pure policy collaborators; packets are untrusted.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import threading
from typing import Callable


FORMAT = "ywe.scoped_commit_journal.v1"
MAX_VALUE_BYTES = 65536
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
MAX_ENTRIES = 128
MAX_INTEGER = 9007199254740991
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_SCOPES = frozenset({"shared_worldstate", "leaf_branch_state", "player_state", "player_perception"})


class JournalError(ValueError):
    """Stable protocol failure code; no packet or reducer exception text escapes."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _identifier(value: str) -> None:
    if type(value) is not str or _IDENTIFIER.fullmatch(value) is None:
        raise JournalError("INVALID_VALUE")


def _integer(value: int, maximum: int) -> None:
    if type(value) is not int or not 0 <= value <= maximum:
        raise JournalError("INVALID_VALUE")


def _encode(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def _object_bytes(value: dict) -> bytes:
    if type(value) is not dict:
        raise JournalError("INVALID_VALUE")
    pending = [(value, 0)]
    count = 0
    while pending:
        item, depth = pending.pop()
        count += 1
        if count > 4096 or depth > 32:
            raise JournalError("VALUE_LIMIT")
        if item is None or type(item) is bool:
            continue
        if type(item) is int:
            if abs(item) > MAX_INTEGER:
                raise JournalError("INVALID_VALUE")
        elif type(item) is str:
            try:
                size = len(item.encode("utf-8"))
            except UnicodeError:
                raise JournalError("INVALID_VALUE") from None
            if size > MAX_VALUE_BYTES:
                raise JournalError("VALUE_LIMIT")
        elif type(item) is list:
            if len(item) > 4096:
                raise JournalError("VALUE_LIMIT")
            pending.extend((child, depth + 1) for child in item)
        elif type(item) is dict:
            if len(item) > 4096 or any(type(key) is not str for key in item):
                raise JournalError("INVALID_VALUE")
            pending.extend((child, depth + 1) for pair in item.items() for child in pair)
        else:
            raise JournalError("INVALID_VALUE")
    encoded = _encode(value)
    if len(encoded) > MAX_VALUE_BYTES:
        raise JournalError("VALUE_LIMIT")
    return encoded


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise JournalError("INVALID_ARCHIVE")
        result[key] = value
    return result


def _reject_number(token: str) -> None:
    raise JournalError("INVALID_ARCHIVE")


def _parse_integer(token: str) -> int:
    if len(token.lstrip("-")) > 16:
        raise JournalError("INVALID_ARCHIVE")
    number = int(token)
    if abs(number) > MAX_INTEGER:
        raise JournalError("INVALID_ARCHIVE")
    return number


@dataclass(frozen=True)
class TruthScope:
    world_id: str
    truth_scope: str
    subject_id: str

    def __post_init__(self) -> None:
        _identifier(self.world_id)
        _identifier(self.subject_id)
        if type(self.truth_scope) is not str or self.truth_scope not in _SCOPES:
            raise JournalError("INVALID_SCOPE")
        if self.truth_scope == "shared_worldstate" and self.subject_id != self.world_id:
            raise JournalError("INVALID_SCOPE")

    def to_record(self) -> dict:
        return {"world_id": self.world_id, "truth_scope": self.truth_scope, "subject_id": self.subject_id}


@dataclass(frozen=True)
class CommitReceipt:
    revision: int
    entry_digest: str
    state_digest: str


Reducer = Callable[[TruthScope, dict, dict], dict]


class CommitJournal:
    """Serializes one owner's pure reductions; all public state is detached."""

    def __init__(self, scope: TruthScope, policy_id: str, initial_state: dict, reducer: Reducer):
        if type(scope) is not TruthScope:
            raise JournalError("INVALID_SCOPE")
        _identifier(policy_id)
        if not callable(reducer):
            raise JournalError("INVALID_POLICY")
        self._scope = scope
        self._policy_id = policy_id
        self._initial = _object_bytes(initial_state)
        self._reducer = reducer
        self._genesis = _hash(_encode(self._header()))
        self._lock = threading.RLock()
        self._reducing = False
        self._reentry = False
        # One assignment publishes state, history and retry identities together.
        self._snapshot = (self._initial, (), {})

    def _header(self) -> dict:
        return {"format": FORMAT, "scope": self._scope.to_record(), "policy_id": self._policy_id,
                "initial_state": json.loads(self._initial)}

    def _guard(self) -> None:
        if self._reducing:
            self._reentry = True
            raise JournalError("REENTRANT_ACCESS")

    def state(self) -> dict:
        with self._lock:
            self._guard()
            return json.loads(self._snapshot[0])

    def head(self) -> str:
        with self._lock:
            self._guard()
            entries = self._snapshot[1]
            return json.loads(entries[-1])["entry_digest"] if entries else self._genesis

    def save(self) -> bytes:
        with self._lock:
            self._guard()
            state, entries, _ = self._snapshot
            return _encode({**self._header(), "entries": [json.loads(entry) for entry in entries],
                            "final_state": json.loads(state)})

    def commit(self, request_id: str, expected_revision: int, packet: dict,
               compensates: str | None = None) -> CommitReceipt:
        _identifier(request_id)
        _integer(expected_revision, MAX_ENTRIES)
        if compensates is not None:
            _identifier(compensates)
        request = {"request_id": request_id, "expected_revision": expected_revision,
                   "packet": json.loads(_object_bytes(packet)), "compensates": compensates}
        fingerprint = _encode(request)
        with self._lock:
            self._guard()
            state, entries, requests = self._snapshot
            if request_id in requests:
                original, receipt = requests[request_id]
                if original != fingerprint:
                    raise JournalError("IDENTITY_CONFLICT")
                return receipt
            if expected_revision != len(entries):
                raise JournalError("REVISION_CONFLICT")
            if len(entries) >= MAX_ENTRIES:
                raise JournalError("CAPACITY_EXCEEDED")
            if compensates is not None and compensates not in requests:
                raise JournalError("UNKNOWN_COMPENSATION")
            self._reducing, self._reentry = True, False
            try:
                next_state = _object_bytes(self._reducer(self._scope, json.loads(state),
                                                       json.loads(_encode(request["packet"]))))
                if self._reentry:
                    raise JournalError("REENTRANT_ACCESS")
            except Exception:
                raise JournalError("POLICY_REJECTED") from None
            finally:
                self._reducing = False
            body = {**request, "revision": len(entries) + 1,
                    "previous_digest": json.loads(entries[-1])["entry_digest"] if entries else self._genesis,
                    "before_state_digest": _hash(state), "after_state_digest": _hash(next_state)}
            digest = _hash(_encode(body))
            entry = _encode({**body, "entry_digest": digest})
            receipt = CommitReceipt(len(entries) + 1, digest, _hash(next_state))
            self._snapshot = (next_state, entries + (entry,), {**requests, request_id: (fingerprint, receipt)})
            return receipt

    @classmethod
    def load(cls, raw: bytes, scope: TruthScope, policy_id: str, reducer: Reducer,
             trusted_head: str) -> CommitJournal:
        """Rebuild privately; cached state and a self-supplied hash confer no trust."""
        if type(raw) is not bytes or len(raw) > MAX_ARCHIVE_BYTES:
            raise JournalError("INVALID_ARCHIVE")
        if type(trusted_head) is not str or _DIGEST.fullmatch(trusted_head) is None:
            raise JournalError("INVALID_TRUSTED_HEAD")
        if type(scope) is not TruthScope:
            raise JournalError("INVALID_SCOPE")
        _identifier(policy_id)
        try:
            archive = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                                 parse_float=_reject_number, parse_constant=_reject_number,
                                 parse_int=_parse_integer)
            if type(archive) is not dict or set(archive) != {
                    "format", "scope", "policy_id", "initial_state", "entries", "final_state"}:
                raise JournalError("INVALID_ARCHIVE")
            if archive["format"] != FORMAT or archive["scope"] != scope.to_record() or archive["policy_id"] != policy_id:
                raise JournalError("ARCHIVE_BINDING_MISMATCH")
            entries = archive["entries"]
            if type(entries) is not list or len(entries) > MAX_ENTRIES:
                raise JournalError("INVALID_ARCHIVE")
            final = _object_bytes(archive["final_state"])
            journal = cls(scope, policy_id, archive["initial_state"], reducer)
            for original in entries:
                if type(original) is not dict or set(original) != {
                        "request_id", "expected_revision", "packet", "compensates", "revision",
                        "previous_digest", "before_state_digest", "after_state_digest", "entry_digest"}:
                    raise JournalError("INVALID_ARCHIVE")
                _integer(original["revision"], MAX_ENTRIES)
                # Check ordinal before commit so a repeated entry cannot replay as a retry.
                if original["revision"] != len(journal._snapshot[1]) + 1:
                    raise JournalError("INVALID_ARCHIVE")
                prior_count = len(journal._snapshot[1])
                journal.commit(original["request_id"], original["expected_revision"],
                               original["packet"], original["compensates"])
                if len(journal._snapshot[1]) != prior_count + 1 or journal._snapshot[1][-1] != _encode(original):
                    raise JournalError("INVALID_ARCHIVE")
            if journal._snapshot[0] != final or journal.head() != trusted_head:
                raise JournalError("INVALID_ARCHIVE")
            return journal
        except (JournalError, ValueError, TypeError, KeyError, UnicodeError, RecursionError):
            raise JournalError("INVALID_ARCHIVE") from None

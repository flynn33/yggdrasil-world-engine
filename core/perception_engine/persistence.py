"""Observer-only M4 persistence reference oracle (YWE-REQ-0053)."""

import copy
import hashlib
import json
import re

from .. import core_values as cv
from ..state_journal import CommitJournal, JournalError, TruthScope, _object_bytes
from .perception import PerceptionEngine


FORMAT = "ywe.perception_state.v1"
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")


def _identifier(value):
    if type(value) is not str or _ID.fullmatch(value) is None:
        raise JournalError("INVALID_VALUE")


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _truth(raw):
    record = json.loads(raw)
    record["facts"] = tuple(cv.DeclaredTruthFact(**fact) for fact in record["facts"])
    return cv.TruthInputSnapshot(**record)


class PerceptionPolicy:
    """Pure observer reduction over privately retained M3 sources and rules."""

    def __init__(self, world_id, observer_id, binding, rules, sources):
        self._scope = TruthScope(world_id, "player_perception", observer_id)
        if type(binding) is not cv.CoreBinding or type(rules) is not tuple or type(sources) is not tuple:
            raise JournalError("INVALID_POLICY")
        if len(rules) > 256 or len(sources) > 128:
            raise JournalError("INVALID_POLICY")
        try:
            cv.revalidate_value(binding)
            self._engine = PerceptionEngine(copy.deepcopy(binding))
            encoded_rules = []
            for rule in rules:
                if type(rule) is not cv.PerceptionRule:
                    raise JournalError("INVALID_POLICY")
                encoded_rules.append(cv.canonical_bytes(rule, limit=65536))
                if sum(map(len, encoded_rules)) > 65536:
                    raise JournalError("INVALID_POLICY")
            self._rules = tuple(encoded_rules)
            self._sources = {}
            total = 0
            for pair in sources:
                if type(pair) is not tuple or len(pair) != 2:
                    raise JournalError("INVALID_POLICY")
                truth, provenance = pair
                if type(truth) is not cv.TruthInputSnapshot or type(provenance) is not cv.CoreProvenance:
                    raise JournalError("INVALID_POLICY")
                truth_raw = cv.canonical_bytes(truth, limit=65536)
                provenance_raw = cv.canonical_bytes(provenance, limit=65536)
                _identifier(truth.snapshot_ref)
                if truth.scope_ref != world_id or truth.snapshot_ref in self._sources:
                    raise JournalError("INVALID_POLICY")
                size = len(truth_raw) + len(provenance_raw)
                total += size
                if size > 65536 or total > 1048576:
                    raise JournalError("INVALID_POLICY")
                self._sources[truth.snapshot_ref] = (truth_raw, provenance_raw)
            policy = {"format": FORMAT, "scope": self._scope.to_record(),
                      "binding": self._engine.configuration().to_record(),
                      "rules": [json.loads(raw) for raw in self._rules]}
            self._policy_id = "perception.v1:" + _digest(json.dumps(
                policy, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii"))
        except cv.CoreContractError:
            raise JournalError("INVALID_POLICY") from None
        self._initial = _object_bytes({"format": FORMAT, "world_id": world_id, "observer_id": observer_id,
                         "truth_substrate_ref": None, "overlay": None, "objective_effects": "NONE"})

    @property
    def scope(self):
        return self._scope

    @property
    def policy_id(self):
        return self._policy_id

    def initial_state(self):
        return json.loads(self._initial)

    def source(self, truth_ref):
        """Return detached retained truth and provenance for trusted composition."""
        _identifier(truth_ref)
        source = self._sources.get(truth_ref)
        if source is None:
            raise JournalError("UNKNOWN_TRUTH")
        return tuple(json.loads(raw) for raw in source)

    def packet(self, request_id, truth_ref):
        _identifier(request_id)
        _identifier(truth_ref)
        source = self._sources.get(truth_ref)
        if source is None:
            raise JournalError("UNKNOWN_TRUTH")
        truth, provenance = source
        return {"request_ref": request_id, "truth_ref": truth_ref,
                "truth_sha256": _digest(truth), "provenance_sha256": _digest(provenance)}

    def reduce(self, state, packet):
        """Compose a bounded next view without mutating either caller input."""
        state = json.loads(_object_bytes(state))
        packet = json.loads(_object_bytes(packet))
        if set(packet) != {
                "request_ref", "truth_ref", "truth_sha256", "provenance_sha256"}:
            raise JournalError("POLICY_REJECTED")
        if packet != self.packet(packet["request_ref"], packet["truth_ref"]):
            raise JournalError("POLICY_REJECTED")
        truth, provenance = self._sources[packet["truth_ref"]]
        request = cv.PerceptionRequest(packet["request_ref"], self._scope.subject_id, _truth(truth),
            tuple(cv.PerceptionRule(**json.loads(raw)) for raw in self._rules),
            cv.CoreProvenance(**json.loads(provenance)))
        result = self._engine.compose_overlay(request)
        if (not self._engine.validate_owned_result(result) or result.status not in ("COMPLETED", "NO_OP")
                or result.effect_status != "NONE" or type(result.value) is not cv.PerceptionOverlay
                or result.value.objective_effects != "NONE"):
            raise JournalError("POLICY_REJECTED")
        return json.loads(_object_bytes({**self.initial_state(), "truth_substrate_ref": packet["truth_ref"],
                "overlay": result.value.to_record()}))


class PerceptionStore:
    """Compatible journal wrapper for one observer's pure composition policy."""

    def __init__(self, world_id, observer_id, binding, rules, sources):
        self._policy = PerceptionPolicy(world_id, observer_id, binding, rules, sources)
        self._scope = self._policy.scope
        self._policy_id = self._policy.policy_id
        self._initial = self._policy.initial_state()
        self._engine = self._policy._engine
        self._journal = CommitJournal(self._scope, self._policy_id, self._initial, self._reduce)

    def _packet(self, request_id, truth_ref):
        return self._policy.packet(request_id, truth_ref)

    def _reduce(self, scope, state, packet):
        if scope != self._scope:
            raise JournalError("POLICY_REJECTED")
        return self._policy.reduce(state, packet)

    def publish(self, request_id, expected_revision, truth_ref):
        packet = self._packet(request_id, truth_ref)
        return self._journal.commit(request_id, expected_revision, packet)

    def state(self):
        return self._journal.state()

    def checkpoint(self):
        return self._journal.checkpoint()

    @classmethod
    def load(cls, raw, trusted_head, world_id, observer_id, binding, rules, sources):
        owner = cls(world_id, observer_id, binding, rules, sources)
        journal = CommitJournal.load(raw, owner._scope, owner._policy_id, owner._reduce, trusted_head)
        archive = json.loads(journal.save())
        if archive["initial_state"] != owner._initial or any(
                entry["request_id"] != entry["packet"]["request_ref"] or entry["compensates"] is not None
                for entry in archive["entries"]):
            raise JournalError("INVALID_ARCHIVE")
        owner._journal = journal
        return owner

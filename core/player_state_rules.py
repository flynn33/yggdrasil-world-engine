"""Pure player-domain admission rules for YWE-REQ-0056.

Schema validation and qualification of external evidence belong to the aggregate
owner. This policy checks semantic links and transitions without publishing state.
"""

import json
import re

from .state_journal import JournalError, _identifier, _object_bytes


IDENTITY_STATES = ("veiled", "suspected", "fragmented", "named_fragment",
                   "partial_revelation", "coherent_revelation", "integrated")
REVEAL_STATUSES = ("not_revealed", "player_suspects", "fragment_revealed",
                   "name_partially_revealed", "role_partially_revealed",
                   "identity_coherent", "identity_integrated")
ABILITY_STATES = ("latent", "pressured", "eligible", "unlocked", "unstable",
                  "coherent", "mastered", "transformed", "decohered", "sealed")
_PROFILE_KEYS = frozenset(("profile_id", "identity_states", "identity_reveal_statuses",
    "identity_transitions", "ability_states", "ability_transitions", "reversible_slots",
    "raven_companion_id", "wolf_companions"))
_CONTEXT_KEYS = frozenset(("world_id", "player_id", "mortal_identity_ref",
                          "branch_ref", "initial", "evidence_refs"))
_KINDS = frozenset(("celestial", "agent", "branch_history", "plane", "bloodline",
                    "wolf", "raven", "ability", "manifestation", "action", "memory"))
_COEFFICIENT = re.compile(r"(?:0|-?[1-9](?:[0-9]*[1-9])?)\Z")


def _require(condition):
    if not condition:
        raise JournalError("POLICY_REJECTED")


def _refs(value, minimum=0, maximum=128):
    _require(type(value) is list and minimum <= len(value) <= maximum)
    for ref in value:
        _identifier(ref)
    _require(len(set(value)) == len(value))
    return set(value)


def _text(value):
    _require(type(value) is str and bool(value.strip()))


def _prefix(before, after):
    _require(type(before) is list and type(after) is list and after[:len(before)] == before)


def _edges(rows, states):
    _require(type(rows) is list and 1 <= len(rows) <= len(states) * (len(states) - 1))
    edges = set()
    for row in rows:
        _require(type(row) is dict and set(row) == {"from_state", "to_state"})
        pair = row["from_state"], row["to_state"]
        _require(all(type(state) is str and state in states for state in pair)
                 and pair[0] != pair[1] and pair not in edges)
        edges.add(pair)
    reached = {states[0]}
    while True:
        expanded = reached | {target for source, target in edges if source in reached}
        if expanded == reached:
            break
        reached = expanded
    _require(reached == set(states))
    return frozenset(edges)


class PlayerDomainPolicy:
    """Detached, bounded profile policy; successful validation returns None."""

    def __init__(self, profile):
        try:
            profile = json.loads(_object_bytes(profile))
            _require(set(profile) == _PROFILE_KEYS)
            _identifier(profile["profile_id"])
            _identifier(profile["raven_companion_id"])
            _require(profile["identity_states"] == list(IDENTITY_STATES)
                     and profile["ability_states"] == list(ABILITY_STATES)
                     and profile["identity_reveal_statuses"] == dict(zip(IDENTITY_STATES, REVEAL_STATUSES)))
            _refs(profile["reversible_slots"], 0, 3)
            _require(set(profile["reversible_slots"]) <= {"plane", "bloodline", "wolf"})
            _refs(profile["wolf_companions"], 1, 16)
            self._identity_edges = _edges(profile["identity_transitions"], IDENTITY_STATES)
            _require(all(IDENTITY_STATES.index(source) < IDENTITY_STATES.index(target)
                         for source, target in self._identity_edges))
            self._ability_edges = _edges(profile["ability_transitions"], ABILITY_STATES)
            _require(any(source == "decohered" and target != "sealed"
                         for source, target in self._ability_edges))
            _require(any(source == "sealed" for source, _ in self._ability_edges))
            self._profile = _object_bytes(profile)
        except (JournalError, KeyError, TypeError, ValueError, RecursionError):
            raise JournalError("POLICY_REJECTED") from None

    def _context(self, context):
        _object_bytes(context)
        _require(set(context) == _CONTEXT_KEYS and type(context["initial"]) is bool)
        for key in ("world_id", "player_id", "mortal_identity_ref", "branch_ref"):
            _identifier(context[key])
        _refs(context["evidence_refs"])

    def validate(self, kind, document, context):
        try:
            self._context(context)
            _object_bytes(document)
            _require(type(kind) is str and kind in _KINDS)
            self._validate(kind, document, context)
        except (JournalError, KeyError, TypeError, ValueError, RecursionError, AttributeError):
            raise JournalError("POLICY_REJECTED") from None

    def _validate(self, kind, doc, context):
        profile = json.loads(self._profile)
        initial = context["initial"]
        if kind == "celestial":
            state = doc["identity_state"]
            _require(type(state) is str and state in IDENTITY_STATES
                     and doc["reveal_status"] == profile["identity_reveal_statuses"][state])
            _refs(doc["evidence_refs"], 0 if state == "veiled" else 1)
            fragments = doc.get("known_fragments", [])
            _require(type(fragments) is list and len(fragments) <= 128)
            seen = set()
            for fragment in fragments:
                _identifier(fragment["fragment_id"])
                _require(fragment["fragment_id"] not in seen)
                seen.add(fragment["fragment_id"])
                _refs(fragment["source_refs"], 1)
            for key in ("celestial_name_ref", "epithet_ref", "last_reveal_event_ref"):
                if key in doc:
                    _identifier(doc[key])
            if initial:
                _require(state == "veiled" and not fragments and not any(
                    key in doc for key in ("celestial_name_ref", "epithet_ref", "last_reveal_event_ref")))
        elif kind == "agent":
            _identifier(doc["agent_id"])
            _require(doc["current_leaf_branch_ref"] == context["branch_ref"])
            if "mortal_instance_id" in doc:
                _require(doc["mortal_instance_id"] == context["mortal_identity_ref"])
            if initial:
                _require(doc["agent_kind"] == "player_mortal_instance")
            _refs(doc["asp_resilience"]["asp_diagnostic_refs"], 1)
        elif kind == "branch_history":
            _require(doc["player_id"] == context["player_id"]
                     and doc["current_leaf_branch_ref"] == context["branch_ref"])
            entries = doc["entries"]
            _require(type(entries) is list and len(entries) <= 128)
            seen = set()
            for entry in entries:
                for key in ("branch_event_ref", "leaf_branch_ref", "source_action_trace_ref"):
                    _identifier(entry[key])
                _text(entry["chosen_action"])
                _refs(entry["source_refs"], 1)
                _require(entry["branch_event_ref"] not in seen)
                seen.add(entry["branch_event_ref"])
            if entries:
                _require(entries[-1]["leaf_branch_ref"] == context["branch_ref"])
        elif kind == "plane":
            _refs(doc["source_refs"], 1)
            _require(type(doc["planes"]) is dict and 1 <= len(doc["planes"]) <= 128)
            for plane, signal in doc["planes"].items():
                _identifier(plane)
                _refs(signal["source_refs"], 1)
                _require(type(signal["score_q6"]) is int and 0 <= signal["score_q6"] <= 1000000)
        elif kind == "bloodline":
            _refs(doc["source_refs"], 1)
            _require(type(doc["signals"]) is list and len(doc["signals"]) <= 128)
            seen = set()
            for signal in doc["signals"]:
                _identifier(signal["bloodline_id"])
                _require(signal["bloodline_id"] not in seen)
                seen.add(signal["bloodline_id"])
                _refs(signal["source_refs"], 1)
                _require(type(signal["score_q6"]) is int and 0 <= signal["score_q6"] <= 1000000)
                if initial:
                    _require(signal["status"] in ("unknown", "dormant")
                             and signal["revealed_to_player"] is False)
        elif kind == "wolf":
            _refs(doc["source_refs"], 1)
            for channel in ("white_wolf", "dark_wolf", "twin_coherence"):
                signal = doc[channel]
                _refs(signal["source_refs"], 1)
                value = signal["coherence_q6" if channel == "twin_coherence" else "resonance_q6"]
                _require(type(value) is int and 0 <= value <= 1000000)
                if initial and channel != "twin_coherence":
                    _require(signal["signal_state"] == "latent")
        elif kind == "raven":
            _require(doc["companion_id"] == profile["raven_companion_id"]
                     and doc["bound_player_identity"] == context["mortal_identity_ref"]
                     and doc["presence_rule"] == "always_with_player")
            _refs(doc["source_refs"], 1)
            _text(doc["absence_rule"])
            if initial and doc["runtime_status"] == "story_separated":
                _refs(context["evidence_refs"], 1)
        elif kind == "ability":
            _require(doc["player_id"] == context["player_id"] and doc["branch_ref"] == context["branch_ref"]
                     and doc["current_state"] in ABILITY_STATES)
            _identifier(doc["ability_id"])
            _refs(doc["source_refs"], 1)
            _refs(doc["history_refs"])
            _refs(doc["sealed_reason_refs"], 1 if doc["current_state"] == "sealed" else 0)
            if initial:
                _require(doc["current_state"] == "latent")
            if "coherence" in doc:
                coherence = doc["coherence"]
                _require(type(coherence) is dict and set(coherence) == {"coefficient", "exponent", "status"})
                coefficient = coherence["coefficient"]
                _require(type(coefficient) is str and len(coefficient) <= 128
                         and _COEFFICIENT.fullmatch(coefficient) is not None)
                _require(type(coherence["exponent"]) is int and -10000 <= coherence["exponent"] <= 10000)
                _require(coefficient != "0" or coherence["exponent"] == 0)
                _text(coherence["status"])
        elif kind == "manifestation":
            companions = _refs(doc["manifesting_companions"], 1, 16)
            _require(companions <= set(profile["wolf_companions"]))
            _identifier(doc["manifestation_event_id"])
            _refs(doc["source_refs"], 1)
            criteria = doc["manifestation_trigger"]["criteria_met"]
            _require(type(criteria) is list and 1 <= len(criteria) <= 128)
            for criterion in criteria:
                _text(criterion)
            _text(doc["manifestation_duration"]["begins_at"])
            _text(doc["manifestation_duration"]["ends_at"])
            _require(doc["manifestation_duration"]["begins_at"] != doc["manifestation_duration"]["ends_at"])
            _text(doc["dismissal_condition"])
            _require(not initial)
        elif kind == "action":
            _identifier(doc["action_trace_id"])
            _require(doc["player_id"] == context["player_id"] and doc["branch_ref"] == context["branch_ref"]
                     and doc["significance"] in ("meaningful", "branch_forming", "mythic", "prophetic"))
            _refs(doc["source_refs"], 1)
        elif kind == "memory":
            _identifier(doc["memory_id"])
            _identifier(doc["source_action_trace_ref"])
            _refs(doc["source_refs"], 1)
            if "branch_ref" in doc:
                _require(doc["branch_ref"] == context["branch_ref"])

    def transition(self, kind, before, after, context, condition_refs):
        try:
            self.validate(kind, after, {**context, "initial": False})
            _require(context["initial"] is False)
            qualified = _refs(context["evidence_refs"], 1)
            conditions = _refs(condition_refs)
            _require(conditions <= qualified)
            if before is None:
                _require(kind == "ability" and after["current_state"] == "latent")
                _require(bool(set(after["source_refs"]) & qualified))
                return
            # The predecessor may belong to the prior branch in a branch transfer.
            prior_context = {**context, "initial": False}
            if kind == "agent":
                prior_context["branch_ref"] = before["current_leaf_branch_ref"]
            elif kind == "branch_history":
                prior_context["branch_ref"] = before["current_leaf_branch_ref"]
            elif kind == "ability":
                prior_context["branch_ref"] = before["branch_ref"]
            self.validate(kind, before, prior_context)
            if kind == "celestial":
                pair = before["identity_state"], after["identity_state"]
                _require(pair[0] == pair[1] or pair in self._identity_edges)
                _prefix(before.get("known_fragments", []), after.get("known_fragments", []))
                _prefix(before["evidence_refs"], after["evidence_refs"])
                for key in ("celestial_name_ref", "epithet_ref"):
                    _require(key not in before or after.get(key) == before[key])
                _require(bool((set(after["evidence_refs"]) - set(before["evidence_refs"])) & qualified))
            elif kind == "raven":
                if before["runtime_status"] != after["runtime_status"] and "story_separated" in (
                        before["runtime_status"], after["runtime_status"]):
                    _require(bool(conditions))
            elif kind == "ability":
                _require(before["ability_id"] == after["ability_id"])
                pair = before["current_state"], after["current_state"]
                _require(pair[0] == pair[1] or pair in self._ability_edges)
                _prefix(before["history_refs"], after["history_refs"])
                if pair[0] != pair[1] or before["branch_ref"] != after["branch_ref"]:
                    _require(len(after["history_refs"]) > len(before["history_refs"]))
                    _require(bool(set(after["history_refs"][len(before["history_refs"]):]) & qualified))
                if pair[1] == "transformed" or before["branch_ref"] != after["branch_ref"]:
                    _require(set(before["source_refs"]) <= set(after["source_refs"]))
                if pair[0] == "sealed" and pair[1] != "sealed":
                    _require(bool(conditions))
            elif kind == "agent":
                _require(before["agent_id"] == after["agent_id"])
            elif kind == "branch_history":
                _prefix(before["entries"], after["entries"])
        except (JournalError, KeyError, TypeError, ValueError, RecursionError, AttributeError):
            raise JournalError("POLICY_REJECTED") from None

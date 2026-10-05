from __future__ import annotations

import copy
import dataclasses
import hashlib
from functools import lru_cache
import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import unittest
from unittest import mock

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from core.ash_pattern_engine import diagnostics_values as dv
from core.ash_pattern_engine import normalization_values as nv
from core.ash_pattern_engine import recovery_values as rv
from core.ash_pattern_engine import state_values as sv
from core.ash_pattern_engine.fallback_registry import FallbackRegistry
from core.ash_pattern_engine.recovery import RecoveryEngine
from core.ash_pattern_engine.state_model import RecordingDiagnosticCapture, StateModel


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / 'core/ash_pattern_engine/canonical'
LEGACY_REVISION = 'c78ee7e451e5d35b2f615369433291007e7ee261'
CURRENT_AGGREGATE = '76d59926ce9676b7584c6cdd555f50f56fceda075fa3fc8b37167fd2be43f7c9'
DEPENDENCY = 'ash_cosmological_model.f2_9.canonical'
AGGREGATE = '0ed4b3524f5c079298a1d8fd99bdc972992b51ea073111ff4c1bfd91930f0feb'
CODEWORD_PIN = '8836c19481b82ce2b4b89fb48911f1b3d37d315e2099af091c69dbaf1d382f0c'
POLICY_PIN = '00fcee810c5cd445dd0baaaf98c754000347489001e21588eb03afdd1e1ebb95'
N1_POLICY_PIN = '804eec92cf52b465b7aaf0cb5f139f581ac2899d13203a8c4cfe9f4d7579c383'
MATH_PIN = 'ded22332eaf789af79cf71534876051ecb96dc26a7254160b081cd588ae41725'
SOURCE_FIELDS = {
    'state_space_sha256': 'core/ash-state-space.pseudo.md',
    'codeword_source_sha256': 'core/codeword-set.pseudo.md',
    'validity_source_sha256': 'core/state-validity-diagnostics.pseudo.md',
    'classification_source_sha256': 'core/system-state-classification.pseudo.md',
    'recovery_source_sha256': 'core/recoverability-semantics.pseudo.md',
    'diagnostic_source_sha256': 'interfaces/diagnostic-schema.md',
    'taxonomy_source_sha256': 'interfaces/rule-id-taxonomy.md',
}
DIAGNOSIS_RULES = ('ASH-STATE-STRUCTURE-001', 'ASH-ADMISSIBILITY-CLASSIFICATION-001',
                   'ASH-STATE-VALIDITY-001')
CATEGORIES = {'STABLE': 'NO_ACTION', 'UNSTABLE': 'NORMALIZE_STATE',
              'CORRECTABLE': 'APPLY_CORRECTION', 'DEGRADED': 'FALLBACK_REQUIRED',
              'CONTAINED': 'CONTAINMENT_REQUIRED', 'FAILED': 'ESCALATION_REQUIRED',
              'SAFE_HALT': 'TERMINAL_NO_RECOVERY'}
SEVERITY = {'INFO': 0, 'WARNING': 1, 'ERROR': 2, 'CRITICAL': 3}


def normalized_hash(path):
    text = path.read_bytes().decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


@lru_cache(maxsize=40)
def legacy_text(repository_path):
    payload = subprocess.check_output(['git', '-C', str(ROOT), 'show',
                                       LEGACY_REVISION + ':' + repository_path])
    return payload.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')


def legacy_source_hash(relative_path):
    return hashlib.sha256(legacy_text('core/ash_pattern_engine/canonical/' + relative_path).encode('utf-8')).hexdigest()


def source_codewords():
    """Integer-XOR oracle parsed from pinned source, without a production oracle."""
    text = legacy_text('core/ash_pattern_engine/canonical/core/codeword-set.pseudo.md')
    rows = re.findall(r'^g([1-4]) = \(([01](?:, [01]){8})\)$', text, re.M)
    if [number for number, _ in rows] != ['1', '2', '3', '4']:
        raise AssertionError('Expected all four independently pinned source generators')
    generators = tuple(int(bits.replace(', ', ''), 2) for _, bits in rows)
    words = {0}
    for generator in generators:
        words |= {word ^ generator for word in tuple(words)}
    enumeration = re.findall(r'^\s*(\d+)\s+\(([01](?:, [01]){8})\)\s+[048]\s*$', text, re.M)
    if [int(number) for number, _ in enumeration] != list(range(16)):
        raise AssertionError('Expected all sixteen independently pinned source members')
    if words != {int(bits.replace(', ', ''), 2) for _, bits in enumeration}:
        raise AssertionError('Source generator closure and complete enumeration differ')
    return generators, tuple(sorted(words))


def ash(integer):
    return sv.AshState(tuple(int(bit) for bit in format(integer, '09b')))


def number(state):
    return int(state.signature, 2)


def canonical_binding(*, current=False):
    return sv.CanonicalAshBinding(dependency_id=DEPENDENCY,
                                 aggregate_sha256=CURRENT_AGGREGATE if current else AGGREGATE,
                                 **{field: normalized_hash(CANONICAL / path) if current else legacy_source_hash(path)
                                    for field, path in SOURCE_FIELDS.items()})


def normalization_policy():
    return nv.NormalizationPolicyBinding('YWE-NORMALIZE-LEXICOGRAPHIC-001', '1.0.0',
                                          'docs/architecture/m3_normalization_policy.md', N1_POLICY_PIN)


def profile(states=(0,), profile_id='n2:test:profile', source=None):
    states = tuple(states)
    if source is None:
        digest = hashlib.sha256(json.dumps(sorted(states), separators=(',', ':')).encode()).hexdigest()
        source = sv.ProfileSourceBinding('tests/test_m3_recovery.py:declared_profile', digest,
                                         profile_id + ':source')
    return sv.AvailableProfileBinding(sv.ValidityProfile(profile_id, source, [ash(n) for n in states]))


def evidence_source(reference='n2:test:source'):
    return rv.EvidenceSourceBinding(reference, hashlib.sha256(reference.encode()).hexdigest(),
                                    reference + ':evidence')


def context(reference):
    return sv.DiagnosticContext(reference, reference + ':input', reference + ':detection',
                                reference + ':classification')


def classification_facts(binding, diagnostic_context, state, known=False, fallback=False, *, canonical=None):
    subject = 'ash_state_' + state.signature if type(state) is sv.AshState else diagnostic_context.original_input_reference
    facts = []
    for name, value in (('correction_path_is_known', known), ('fallback_is_available', fallback)):
        fact_binding = sv.PredicateBinding(
            diagnostic_context.assessment_reference, diagnostic_context.detection_reference, subject,
            binding.profile_id, binding.source_binding.source_sha256,
            DEPENDENCY if canonical is None else canonical.dependency_id,
            AGGREGATE if canonical is None else canonical.aggregate_sha256,
            diagnostic_context.assessment_reference + ':' + name + ':evidence',
        )
        facts.append(sv.NotEvaluatedPredicate(fact_binding, 'Explicitly unconsulted test observation.')
                     if value is None else sv.EvaluatedPredicate(fact_binding, value))
    return sv.ClassificationEvidence(*facts)


def assessment(model, state, reference='n2:origin', known=False, fallback=False, halt=False, contained=False):
    diagnostic_context = context(reference)
    return model.assess(state, context=sv.SystemContext(halt, contained),
                        classification_evidence=classification_facts(model.profile_binding,
                                                                      diagnostic_context, state, known, fallback,
                                                                      canonical=model.canonical_binding),
                        diagnostic_context=diagnostic_context)


def operation(origin, reference='n2:operation', propagation='SAFE', authority='REACHABLE'):
    origin_reference = origin.assessment_binding.assessment_reference
    return rv.RecoveryOperationContext(
        reference, origin_reference,
        rv.ContextObservation(origin.system_context, reference + ':owner', reference + ':context', evidence_source()),
        rv.PropagationEvidence(propagation, reference, origin_reference, evidence_source('n2:propagation'),
                               'Explicit synthetic propagation observation.'),
        rv.ExternalAuthorityEvidence(authority, reference, origin_reference, evidence_source('n2:authority'),
                                     'Explicit synthetic authority observation.'),
    )


def known_correction(origin, chain, target):
    return rv.KnownCorrection(
        correction_reference='n2:known:correction',
        original_assessment_reference=origin.assessment_binding.assessment_reference,
        source_binding=evidence_source('n2:known:path'), profile_id=origin.profile_binding.profile_id,
        profile_source_sha256=origin.profile_binding.source_binding.source_sha256,
        chain=[ash(word) for word in chain], expected_target=ash(target),
        reason='Independently declared source codeword sequence.',
        classification_evidence_reference=origin.classification_evidence.correction_path_is_known.binding.evidence_reference,
        canonical_binding=origin.source_binding,
    )


def unavailable_correction(origin):
    return rv.UnavailableCorrection(origin.assessment_binding.assessment_reference,
                                     evidence_source('n2:known:path'), 'Declared provider unavailable.',
                                     origin.classification_evidence.correction_path_is_known.binding.evidence_reference)


def reflectively_forged(value, **changes):
    """Controlled fault bypasses constructors to exercise use-time validation."""
    result = copy.copy(value)
    for name, child in changes.items():
        object.__setattr__(result, name, child)
    return result


def health():
    return dv.DiagnosticsHealth(
        coverage_status='COMPLETE_DECLARED_REFERENCE_SCOPE', accepted_count=0, rejected_count=0,
        retained_count=0, expired_count=0, lost_count=0, redacted_field_count=0,
        redacted_reference_count=0, last_confirmed_sequence=None, first_unavailable_sequence=None,
        last_unavailable_sequence=None, active_reservations=0, used_bytes=0,
        storage_state='PROTECTED_VERIFIED', last_failure_code=None, missing_sources=(),
        retention_boundaries=(), range_detail_coalesced=False, meta_overflow_count=0,
        counter_states=tuple(dv.DiagnosticCounterState(field, 'EXACT', None) for field in (
            'ACCEPTED', 'REJECTED', 'RETAINED', 'EXPIRED', 'LOST', 'REDACTED_FIELDS',
            'REDACTED_REFERENCES', 'META_OVERFLOW')),
        meta_record_count=0, meta_storage_state='PROTECTED_VERIFIED', fallback_cause_code=None,
    )


class ControlledDiagnostics:
    """A declared fault port, not a protected collector or export qualification."""

    def __init__(self, *, fail=None, mode='REJECTED', admission=None, completion=None, post_capture=None,
                 post_completion=None):
        self.fail = fail
        self.mode = mode
        self.admission = admission
        self.completion = completion
        self.post_capture = post_capture
        self.post_completion = post_completion
        self.records = []
        self.private_records = []
        self.calls = []
        self.scopes = []
        self.children = []
        self.original_records = []
        self.failed_record = None
        self.finish_inputs = []
        self.failed = False

    def assessment_capture(self, *, relation=None):
        owner = self
        class Capture:
            def begin(self, assessment_reference):
                owner.calls.append(('assessment.begin', assessment_reference, relation))
                target = owner.original_records if relation is None else []
                if relation is not None:
                    owner.children.append((relation, target))
                class Scope:
                    def append(self, emission):
                        if relation is not None and owner.post_capture:
                            if owner.post_capture == 'THROW':
                                raise RuntimeError('controlled child capture failure')
                            return sv.CaptureReceipt(emission.diagnostic_reference, owner.post_capture)
                        target.append(emission)
                        return sv.CaptureReceipt(emission.diagnostic_reference, 'CONFIRMED')
                return Scope()
        return Capture()

    def recovery_capture(self):
        return self

    def begin(self, origin, *, operation_reference):
        return self._begin(origin, operation_reference, False)

    def begin_denial(self, origin, *, operation_reference):
        return self._begin(origin, operation_reference, True)

    def _begin(self, origin, reference, denial):
        self.calls.append(('begin_denial' if denial else 'begin', reference))
        if self.admission == 'THROW':
            raise RuntimeError('controlled admission failure')
        if self.admission == 'NONE':
            return None
        if self.admission == 'BAD_SCOPE':
            scope = object()
        else:
            scope = self
        status = self.admission if self.admission in ('REJECTED', 'NOT_CONFIRMED') else 'CONFIRMED'
        refs = tuple(row.diagnostic_reference for row in origin.emitted_diagnostics)
        receipt = dv.RecoveryAdmissionReceipt(
            status, reference, origin.assessment_binding.assessment_reference, refs,
            (1 if denial else 768) if status == 'CONFIRMED' else 0,
            (270336 if denial else 31588352) if status == 'CONFIRMED' else 0,
            None if status == 'CONFIRMED' else 'DIAGNOSTICS_RESERVATION_REFUSED',
        )
        self.scopes.append(scope)
        return (scope if status == 'CONFIRMED' else None), receipt

    def append(self, record):
        self.calls.append(('append', record))
        if not self.failed and self.fail is not None and self.fail(record):
            self.failed = True
            self.failed_record = record
            if self.mode == 'THROW_AFTER':
                self.private_records.append(record)
            if self.mode in ('THROW_BEFORE', 'THROW_AFTER'):
                raise RuntimeError('controlled immediate capture failure')
            if self.mode == 'NONE':
                return None
            if self.mode == 'WRONG_REFERENCE':
                return sv.CaptureReceipt(record.diagnostic_reference + ':wrong', 'CONFIRMED')
            return sv.CaptureReceipt(record.diagnostic_reference, self.mode)
        self.records.append(record)
        self.private_records.append(record)
        return sv.CaptureReceipt(record.diagnostic_reference, 'CONFIRMED')

    def _completion(self, reference, outcome='COMPLETED', *, apply_fault=True):
        mode = self.completion if apply_fault else self.post_completion
        if mode == 'THROW':
            raise RuntimeError('controlled finish failure')
        if mode == 'NONE':
            return None
        status = 'INCOMPLETE' if mode == 'INCOMPLETE' else 'COMPLETE'
        return dv.DiagnosticsCompletionReceipt(
            reference + ':wrong' if mode == 'WRONG_REFERENCE' else reference,
            status, outcome, tuple(range(len(self.records))),
            'PARTIAL' if status == 'INCOMPLETE' else 'COMPLETE_DECLARED_REFERENCE_SCOPE',
            'DIAGNOSTICS_COMPLETION_MISMATCH' if status == 'INCOMPLETE' else None,
            None, health(),
        )

    def complete_assessment(self, result):
        self.calls.append(('complete_assessment', result))
        return self._completion(result.assessment_binding.assessment_reference, apply_fault=False)

    def complete_normalization(self, result):
        raise AssertionError('N2 replays validated N1 proof under its own capture; no N1 operation is substituted')

    def finish(self, result):
        self.calls.append(('finish', result))
        self.finish_inputs.append(result)
        return self._completion(result.operation_context.operation_reference)


class CorrectionProvider:
    def __init__(self, result=None, *, throw=False):
        self.result, self.throw, self.calls = result, throw, []

    def resolve(self, origin, *, operation_context):
        self.calls.append((origin, operation_context))
        if self.throw:
            raise RuntimeError('controlled correction port failure')
        return unavailable_correction(origin) if self.result is None else self.result


class NormalizationResolver:
    def __init__(self, model, mode='READY'):
        self.model, self.mode, self.calls = model, mode, []

    def resolve(self, origin, *, operation_context, policy_binding):
        self.calls.append((origin, operation_context))
        if self.mode == 'THROW':
            raise RuntimeError('controlled normalization resolver failure')
        if self.mode == 'NONE':
            return None
        diagnosis = self.model.diagnosis_from_assessment(origin)
        observation = rv.NormalizationResolutionObservation(
            'UNAVAILABLE' if self.mode == 'UNAVAILABLE' else 'READY',
            operation_context.operation_reference, origin.assessment_binding.assessment_reference,
            evidence_source('n2:normalization:resolver'), 'Explicit resolution observation.')
        if self.mode == 'UNAVAILABLE':
            return rv.NormalizationPreparation('UNAVAILABLE', diagnosis, policy_binding, None, None, None,
                                               observation)
        plan = self.model.plan_normalization(diagnosis, plan_reference='n2:normalization:plan',
                                             evidence_reference='n2:normalization:proof', policy_binding=policy_binding)
        if self.mode == 'BAD_PROOF':
            plan = dataclasses.replace(plan, selected_target=ash(source_codewords()[0][1]),
                                       codeword_chain=(ash(source_codewords()[0][0] ^ source_codewords()[0][1]),))
        validation = self.model.validate_normalization_plan(plan)
        return rv.NormalizationPreparation('READY', diagnosis, policy_binding, plan, validation, None, observation)


class Conditions:
    def __init__(self, values=None, mode=None):
        self.values, self.mode, self.calls = {} if values is None else values, mode, []

    def evaluate(self, condition, *, origin, entry, phase, operation_context):
        self.calls.append((entry.policy_id, phase, condition.condition_id))
        if self.mode == 'THROW':
            raise RuntimeError('controlled condition port failure')
        status = self.values.get(condition.condition_id, 'TRUE')
        source = evidence_source('n2:condition:provider')
        observation = rv.PredicateObservation(
            status, condition, operation_context.operation_reference, origin.assessment_binding.assessment_reference,
            'n2:registry', evidence_source('n2:registry:source').source_sha256,
            entry.policy_id, phase, entry.candidate_state_reference, source,
            'Explicit synthetic condition observation.',
        )
        if self.mode == 'BAD_BINDING':
            observation = dataclasses.replace(observation, policy_id='FALLBACK-STATE-999')
        return observation


class PostFacts:
    def __init__(self, binding, *, halt=False, contained=False, mode=None):
        self.binding, self.halt, self.contained, self.mode, self.calls = binding, halt, contained, mode, []

    def provide(self, candidate, *, origin, action_reference, diagnostic_context, operation_context):
        self.calls.append((candidate, action_reference, diagnostic_context))
        if self.mode == 'THROW':
            raise RuntimeError('controlled post facts failure')
        if self.mode == 'UNAVAILABLE':
            return rv.UnavailablePostAssessmentFacts(operation_context.operation_reference, candidate,
                                                     evidence_source('n2:post:facts'), 'Declared post facts unavailable.')
        facts = classification_facts(self.binding, diagnostic_context, candidate, None, None,
                                     canonical=origin.source_binding)
        if self.mode == 'BAD_BINDING':
            bad = dataclasses.replace(facts.fallback_is_available.binding, subject_reference='ash_state_111111111')
            facts = dataclasses.replace(facts, fallback_is_available=sv.NotEvaluatedPredicate(bad, 'Unconsulted bad subject.'))
        return rv.PostAssessmentFacts(
            diagnostic_context,
            rv.ContextObservation(sv.SystemContext(self.halt, self.contained), 'n2:post:owner',
                                  action_reference + ':context', evidence_source('n2:post:context')),
            facts,
        )


def registry(model, entries=(), *, unavailable=False):
    binding = rv.RegistrySourceBinding('n2:registry', evidence_source('n2:registry:source'),
                                       model.profile_binding.profile_id, model.profile_binding.source_binding.source_sha256,
                                       model.canonical_binding.dependency_id, model.canonical_binding.aggregate_sha256)
    if unavailable:
        snapshot = rv.UnavailableFallbackRegistry(binding, 'Explicitly unavailable synthetic registry.')
    else:
        certifications = []
        for index, entry in enumerate(entries):
            cert = assessment(model, entry.candidate_state_reference, reference=f'n2:cert:{index}', known=None, fallback=None)
            observation = rv.ContextObservation(cert.system_context, 'n2:cert:owner', f'n2:cert:{index}:context',
                                                evidence_source('n2:cert:source'))
            certifications.append(rv.CandidateCertification(entry.policy_id, observation, cert))
        snapshot = rv.AvailableFallbackRegistry(binding, tuple(entries), tuple(certifications))
    return FallbackRegistry(snapshot, state_model=model)


def entries_for(statuses=(1, 1, 1)):
    entries, observations = [], {}
    for index in (2, 1, 0):
        policy_id = f'FALLBACK-STATE-{index + 1:03d}'
        conditions = tuple(rv.ConditionReference(policy_id + ':app:' + str(n), evidence_source('n2:condition:source'))
                           for n in range(2))
        validations = (rv.ConditionReference(policy_id + ':validation', evidence_source('n2:condition:source')),)
        status = statuses[index]
        observations[conditions[0].condition_id] = 'TRUE'
        observations[conditions[1].condition_id] = 'FALSE' if status == 0 else 'TRUE'
        observations[validations[0].condition_id] = 'TRUE' if status == 1 else 'FALSE'
        entries.append(rv.FallbackPolicyEntry(policy_id, conditions, ash(0), 2 if index == 2 else 1,
                                              validations, 'ESCALATE_TO_CONTAINMENT' if status == 3 else 'TRY_NEXT',
                                              ('Synthetic source-compatible test entry.',)))
    return tuple(entries), observations


def authored_wire_cases():
    """Build declared transport examples from source arithmetic and literal fields.

    No production constructor, StateModel, RecoveryEngine, registry or serializer
    supplies an expected field. These records do not prove collector effects.
    """
    _, words = source_codewords()
    source = {'dependency_id': DEPENDENCY, 'aggregate_sha256': AGGREGATE,
              **{field: legacy_source_hash(path) for field, path in SOURCE_FIELDS.items()}}
    declared_source = {'source_reference': 'tests/test_m3_recovery.py:authored_profile',
                       'source_sha256': hashlib.sha256(b'[0]').hexdigest(),
                       'evidence_reference': 'n2_authored:profile:evidence'}
    binding = {'availability': 'AVAILABLE', 'profile_id': 'n2_authored:neutral',
               'source_binding': declared_source, 'recognized_valid_signatures': ['000000000']}
    notes = ['Independently declared transport evidence; capture truth is established separately.']
    recovery_rules = ['ASH-RECOVERY-ACTION-001']
    fallback_rules = recovery_rules + ['ASH-FALLBACK-SELECTION-001']
    codeword_rules = recovery_rules + ['ASH-CODEWORD-STRUCTURE-001']
    def state(integer):
        return None if integer is None else {'state_space': 'F2^9', 'bits': [int(b) for b in format(integer, '09b')]}
    def provenance(reference):
        return {'source_reference': reference, 'source_sha256': hashlib.sha256(reference.encode()).hexdigest(),
                'evidence_reference': reference + ':evidence'}
    def diagnostic(integer):
        orbit = {integer ^ word for word in words}
        status = 'VALID' if integer == 0 else 'TRANSFORMATION_COMPATIBLE' if 0 in orbit else 'TRANSFORMATION_INCOMPATIBLE'
        compatibility, normal, relevance, valid = {
            'VALID': ('COMPATIBLE', 'ALREADY_VALID', 'NO_RECOVERY_NEEDED', True),
            'TRANSFORMATION_COMPATIBLE': ('COMPATIBLE', 'NORMALIZABLE', 'RECOVERY_APPLICABLE', False),
            'TRANSFORMATION_INCOMPATIBLE': ('INCOMPATIBLE', 'NOT_NORMALIZABLE', 'NOT_RECOVERABLE', False)}[status]
        return {'input_state': state(integer)['bits'], 'admissibility_status': status,
                'transformation_compatibility': compatibility, 'normalization_status': normal,
                'recoverability_relevance': relevance, 'is_valid': valid,
                'orbit_info': {'orbit_id': format(min(orbit), '09b'), 'member_count': 16,
                               'contains_known_valid_state': 0 in orbit},
                'rule_ids': list(DIAGNOSIS_RULES), 'notes': list(notes)}
    def envelope(reference, parent, root, subject, severity, disposition, rules, *, kind='RECOVERY', stage='RECOVERY'):
        return {'diagnostic_kind': kind, 'severity': severity, 'stage': stage, 'disposition': disposition,
                'subject_reference': subject, 'parent_diagnostic_reference': parent, 'chain_root_reference': root,
                'rule_ids': list(rules), 'summary': 'Independently authored bounded recovery observation.', 'notes': list(notes)}
    def origin(name, integer, *, known=False, fallback=False, halt=False, contained=False):
        reference = 'n2_authored:' + name
        signature = format(integer, '09b'); subject = 'ash_state_' + signature
        diag = diagnostic(integer); semantic = diag['admissibility_status']
        consulted = ([] if halt or contained or semantic == 'VALID' else
                     ['correction_path_is_known' if semantic == 'TRANSFORMATION_COMPATIBLE' else 'fallback_is_available'])
        cls = ('SAFE_HALT' if halt else 'CONTAINED' if contained else 'STABLE' if semantic == 'VALID' else
               ('CORRECTABLE' if known else 'UNSTABLE') if semantic == 'TRANSFORMATION_COMPATIBLE' else
               ('DEGRADED' if fallback else 'FAILED'))
        facts = {}
        for field, value in (('correction_path_is_known', known), ('fallback_is_available', fallback)):
            fact = {'evaluation': 'EVALUATED' if field in consulted else 'NOT_EVALUATED', 'binding': {
                'assessment_reference': reference, 'diagnosis_reference': reference + ':detection',
                'subject_reference': subject, 'profile_id': binding['profile_id'],
                'profile_source_sha256': declared_source['source_sha256'], 'ash_dependency_id': DEPENDENCY,
                'ash_aggregate_sha256': AGGREGATE, 'evidence_reference': reference + ':' + field + ':evidence'}}
            fact.update(value=value) if field in consulted else fact.update(reason='Explicitly unconsulted declared fact.')
            facts[field] = fact
        severity, disposition = {'VALID': ('INFO', 'RESOLVED'), 'TRANSFORMATION_COMPATIBLE': ('WARNING', 'PENDING'),
                                 'TRANSFORMATION_INCOMPATIBLE': ('ERROR', 'BLOCKED')}[semantic]
        detection = {'diagnostic_reference': reference + ':detection', 'envelope': envelope(reference + ':detection',
            None, reference + ':detection', subject, severity, disposition, DIAGNOSIS_RULES, kind='STATE_VALIDITY', stage='DETECTION')}
        class_severity, class_disposition = {'STABLE': ('INFO', 'RESOLVED'), 'UNSTABLE': ('WARNING', 'PENDING'),
            'CORRECTABLE': ('ERROR', 'PENDING'), 'DEGRADED': ('ERROR', 'PENDING'), 'FAILED': ('ERROR', 'BLOCKED'),
            'CONTAINED': ('CRITICAL', 'PENDING'), 'SAFE_HALT': ('CRITICAL', 'TERMINAL')}[cls]
        classification = {'diagnostic_reference': reference + ':classification', 'envelope': envelope(
            reference + ':classification', reference + ':detection', reference + ':detection', subject,
            max((severity, class_severity), key=SEVERITY.__getitem__), class_disposition,
            ['ASH-CLASSIFICATION-MAPPING-001', 'ASH-RECOVERY-ACTION-001'], kind='STATE_VALIDITY', stage='CLASSIFICATION')}
        return {'schema_ref': 'data/schemas/m3_state_assessment_schema.json', 'artifact_type': 'ywe_state_assessment',
                'artifact_version': '1.0.0', 'outcome': 'assessment', 'assessment_binding': {
                    'assessment_reference': reference, 'original_input_reference': reference + ':input',
                    'diagnosis_reference': reference + ':detection'}, 'source_binding': copy.deepcopy(source),
                'profile_binding': copy.deepcopy(binding), 'input_evidence': {
                    'original_input_reference': reference + ':input', 'representation_kind': 'SIGNATURE',
                    'observed_length': 9, 'length_unit': 'CHARACTERS', 'preview': signature,
                    'preview_encoding': 'TEXT', 'truncated': False, 'coordinate_observations': [], 'failure_code': None},
                'parsed_state': state(integer), 'state_validity_diagnostic': diag,
                'emitted_diagnostics': [detection, classification],
                'system_context': {'is_in_safe_halt': halt, 'is_in_containment': contained},
                'classification_evidence': facts, 'system_state_class': cls, 'recovery_category': CATEGORIES[cls],
                'consulted_predicates': consulted}
    def validation(assessment):
        return {'status': 'VERIFIED', 'submitted_assessment': copy.deepcopy(assessment),
                'current_source_binding': copy.deepcopy(source), 'current_profile_binding': copy.deepcopy(binding),
                'expected_diagnostic': copy.deepcopy(assessment['state_validity_diagnostic']),
                'expected_system_state_class': assessment['system_state_class'],
                'expected_recovery_category': assessment['recovery_category'],
                'expected_consulted_predicates': list(assessment['consulted_predicates']), 'failure_code': None, 'field_name': None}
    def context_observation(reference, context):
        return {'context': copy.deepcopy(context), 'owner_reference': reference + ':owner',
                'observation_reference': reference + ':observation', 'source_binding': provenance(reference + ':source')}
    def completion(reference, count, *, incomplete=False):
        return {'operation_reference': reference, 'status': 'INCOMPLETE' if incomplete else 'COMPLETE',
                'operation_outcome': 'FAILED' if incomplete else 'COMPLETED', 'confirmed_event_indices': list(range(count)),
                'diagnostic_coverage': 'PARTIAL' if incomplete else 'COMPLETE_DECLARED_REFERENCE_SCOPE',
                'failure_code': 'DIAGNOSTICS_COMPLETION_MISMATCH' if incomplete else None, 'attempted_event_index': None,
                'health': {'coverage_status': 'COMPLETE_DECLARED_REFERENCE_SCOPE', 'accepted_count': count, 'rejected_count': 0,
                    'retained_count': count, 'expired_count': 0, 'lost_count': 0, 'redacted_field_count': 0,
                    'redacted_reference_count': 0, 'last_confirmed_sequence': count - 1 if count else None,
                    'first_unavailable_sequence': None, 'last_unavailable_sequence': None, 'active_reservations': 0,
                    'used_bytes': 0, 'storage_state': 'PROTECTED_VERIFIED', 'last_failure_code': None, 'missing_sources': [],
                    'retention_boundaries': [], 'range_detail_coalesced': False, 'meta_overflow_count': 0,
                    'counter_states': [{'field': counter, 'status': 'EXACT', 'reason': None} for counter in (
                        'ACCEPTED', 'REJECTED', 'RETAINED', 'EXPIRED', 'LOST', 'REDACTED_FIELDS', 'REDACTED_REFERENCES', 'META_OVERFLOW')],
                    'meta_record_count': 0, 'meta_storage_state': 'PROTECTED_VERIFIED', 'fallback_cause_code': None}}
    contract_paths = ('interfaces/contracts/recovery-engine-contract.md', 'interfaces/contracts/diagnostics-module-contract.md',
        'registries/fallback-policy-registry.md', 'algorithms/recovery-fallback-semantics.pseudo.md',
        'algorithms/containment-safe-failure-semantics.pseudo.md', 'interfaces/diagnostic-schema.md', 'interfaces/rule-id-taxonomy.md')
    def packet(assessment):
        reference = assessment['assessment_binding']['assessment_reference'] + ':operation'
        return {'schema_ref': 'data/schemas/m3_recovery_value_schema.json', 'artifact_type': 'ywe_recovery_value',
                'artifact_version': '1.0.0', 'outcome': 'NO_ACTION', 'execution_scope': 'CORE_REFERENCE_IMMUTABLE_VALUE',
                'operation_context': {'operation_reference': reference,
                    'origin_assessment_reference': assessment['assessment_binding']['assessment_reference'],
                    'context_observation': context_observation(reference, assessment['system_context']),
                    'propagation_evidence': {'status': 'SAFE', 'operation_reference': reference,
                        'origin_assessment_reference': assessment['assessment_binding']['assessment_reference'],
                        'source_binding': provenance(reference + ':propagation'), 'reason': 'Declared safe propagation.'},
                    'external_authority_evidence': {'status': 'REACHABLE', 'operation_reference': reference,
                        'origin_assessment_reference': assessment['assessment_binding']['assessment_reference'],
                        'source_binding': provenance(reference + ':authority'), 'reason': 'Declared reachable authority.'}},
                'origin_assessment': copy.deepcopy(assessment), 'origin_validation': validation(assessment),
                'source_binding': {'canonical_binding': copy.deepcopy(source), 'contract_pins': [
                    {'path': path, 'sha256': legacy_source_hash(path)} for path in contract_paths]},
                'registry_binding': None, 'route_authorization': None, 'steps': [], 'post_assessments': [],
                'policy_attempts': [], 'action_decisions': [], 'emitted_diagnostics': [], 'candidate_state': copy.deepcopy(assessment['parsed_state']),
                'directive': None, 'failure_detail': None, 'normalization_preparation': None, 'correction_observation': None,
                'registry_snapshot': None, 'registry_validation': None, 'completion_observation': None, 'session_effects_performed': False}
    def append(result, payload, disposition='PENDING', *, severity=None, stage='RECOVERY'):
        assessment = result['origin_assessment']; reference = result['operation_context']['operation_reference'] + ':event:' + str(len(result['emitted_diagnostics']))
        previous = (result['emitted_diagnostics'] or assessment['emitted_diagnostics'])[-1]
        severity = max((previous['envelope']['severity'], severity or previous['envelope']['severity']), key=SEVERITY.__getitem__)
        if 'step_index' in payload: payload['diagnostic_reference'] = reference
        record = {'diagnostic_reference': reference, 'envelope': envelope(reference, previous['diagnostic_reference'],
            assessment['assessment_binding']['diagnosis_reference'], 'ash_state_' + ''.join(map(str, assessment['parsed_state']['bits'])),
            severity, disposition, fallback_rules if result['route_authorization'] else codeword_rules if 'codeword' in payload and payload['codeword'] else recovery_rules,
            kind='FALLBACK' if result['route_authorization'] else 'RECOVERY', stage=stage),
            'record_kind': 'ACTION_VALUE_COMPUTED' if 'step_index' in payload else 'OPERATION_DECISION', 'payload': copy.deepcopy(payload)}
        result['emitted_diagnostics'].append(record)
        return record
    def step(result, action, before, after, *, codeword=None, post=None):
        value = {'step_index': len(result['steps']), 'action': action, 'status': 'COMPLETED', 'before_state': state(before),
                 'codeword': state(codeword), 'after_state': state(after), 'policy_id': None, 'predicate_observation': None,
                 'post_assessment_reference': post, 'diagnostic_reference': 'n2_authored:pending',
                 'reason': 'Independently authored exact value step.'}
        append(result, value); result['steps'].append(value)
    def decision(result, action, outcome, *, target=None, policy_id=None, post=None, directive=None):
        assessment = result['origin_assessment']; reference = result['operation_context']['operation_reference'] + ':action:' + str(len(result['action_decisions']))
        canonical_action = {'NO_ACTION': 'no-action', 'CORRECT': 'correct', 'NORMALIZE': 'normalize',
                            'FALLBACK_CANDIDATE': 'select-fallback', 'FALLBACK_SUMMARY': 'fallback-summary', 'HANDOFF': 'handoff'}[action]
        previous_indices = result['action_decisions'][-1]['step_indices'] if result['action_decisions'] else []
        first_index = previous_indices[-1] + 1 if previous_indices else 0
        indices = list(range(0 if action == 'FALLBACK_SUMMARY' else first_index, len(result['steps'])))
        step_names = {'NORMALIZE_PLAN': 'resolve-normalization', 'NORMALIZE_XOR': 'normalize',
            'CORRECTION_RESOLVE': 'resolve-correction', 'CORRECTION_XOR': 'correct',
            'FALLBACK_SELECT': 'select-fallback', 'POST_ASSESSMENT': 'validate-recovery'}
        canonical_steps = ([{'action': step_names[result['steps'][i]['action']], 'status': result['steps'][i]['status'],
                             'reason': result['steps'][i]['reason']} for i in indices]
                           if action != 'FALLBACK_SUMMARY' else [])
        value = {'action_reference': reference, 'action': action, 'diagnostic': {
            'recovery_category': assessment['recovery_category'], 'original_state_class': assessment['system_state_class'],
            'original_diagnostic': copy.deepcopy(assessment['state_validity_diagnostic']),
            'steps': canonical_steps or [{'action': canonical_action, 'status': 'COMPLETED', 'reason': 'Declared completed action decision.'}],
            'outcome': outcome, 'corrected_state': state(target), 'fallback_policy_id': policy_id,
            'reason': 'Independently declared complete action outcome.', 'rule_ids': fallback_rules if policy_id else recovery_rules},
            'step_indices': indices, 'post_assessment_reference': post,
            'candidate_context': {'is_in_safe_halt': False, 'is_in_containment': False} if post else None,
            'directive': copy.deepcopy(directive)}
        disposition = 'RESOLVED' if outcome in ('RECOVERED', 'RECOVERED_VIA_FALLBACK', 'NOT_APPLICABLE') else 'BLOCKED'
        append(result, value, disposition); result['action_decisions'].append(value)
        return value
    def post(result, integer, action_reference):
        child = origin(result['operation_context']['operation_reference'] + ':post', integer)
        result['post_assessments'].append({'link': {'parent_operation_reference': result['operation_context']['operation_reference'],
            'parent_action_reference': action_reference, 'originating_chain_root_reference': result['origin_assessment']['assessment_binding']['diagnosis_reference']},
            'candidate_state': state(integer), 'context_observation': context_observation(child['assessment_binding']['assessment_reference'], child['system_context']),
            'assessment': child, 'capture_status': 'COMPLETE'})
        return child['assessment_binding']['assessment_reference']
    def finish(result):
        result['completion_observation'] = completion(result['operation_context']['operation_reference'], len(result['emitted_diagnostics']))
        return result
    registry_binding = {'registry_id': 'n2_authored:registry', 'source_binding': provenance('n2_authored:registry:source'),
        'profile_id': binding['profile_id'], 'profile_source_sha256': declared_source['source_sha256'],
        'ash_dependency_id': DEPENDENCY, 'ash_aggregate_sha256': AGGREGATE, 'source_verification': 'DECLARED_NOT_AUTHENTICATED'}
    registry_header = {'schema_ref': 'data/schemas/m3_fallback_registry_schema.json', 'artifact_type': 'ywe_fallback_registry', 'artifact_version': '1.0.0'}
    entry = {'policy_id': 'FALLBACK-STATE-001', 'applicability_conditions': [], 'candidate_state_reference': state(0),
             'ordering_rank': -(1 << 63), 'validation_requirements': [], 'escalation_on_failure': 'TRY_NEXT', 'notes': list(notes)}
    cert_assessment = origin('certification', 0)
    certification = {'policy_id': entry['policy_id'], 'context_observation': context_observation('n2_authored:certification', cert_assessment['system_context']),
                     'source_assessment': cert_assessment}
    registries = [{**registry_header, 'availability': 'AVAILABLE', 'source_binding': copy.deepcopy(registry_binding),
                   'entries': [entry], 'candidate_certifications': [certification]},
                  {**registry_header, 'availability': 'AVAILABLE', 'source_binding': copy.deepcopy(registry_binding), 'entries': [], 'candidate_certifications': []},
                  {**registry_header, 'availability': 'UNAVAILABLE', 'source_binding': copy.deepcopy(registry_binding), 'reason': 'Declared registry unavailable; empty availability is a different fact.'}]
    def bind_registry(result, snapshot):
        certifications = snapshot.get('candidate_certifications', [])
        result.update(registry_binding=copy.deepcopy(registry_binding), registry_snapshot=copy.deepcopy(snapshot),
                      registry_validation={'status': 'VERIFIED', 'submitted_snapshot': copy.deepcopy(snapshot),
                          'current_source_binding': copy.deepcopy(source), 'current_profile_binding': copy.deepcopy(binding),
                          'candidate_validations': [{'policy_id': cert['policy_id'], 'submitted_certification': copy.deepcopy(cert),
                              'assessment_validation': validation(cert['source_assessment']),
                              'target_diagnostic': copy.deepcopy(cert['source_assessment']['state_validity_diagnostic'])} for cert in certifications],
                          'failure_code': None, 'failed_policy_id': None, 'field_name': None})
        result['route_authorization'] = {'route': 'DIRECT_DEGRADED', 'original_system_state_class': 'DEGRADED',
            'origin_assessment_reference': result['origin_assessment']['assessment_binding']['assessment_reference'],
            'failed_action_decision_reference': None, 'failed_outcome': None, 'rule_ids': fallback_rules,
            'origin_predicate_evidence_reference': result['origin_assessment']['classification_evidence']['fallback_is_available']['binding']['evidence_reference'],
            'active_recovery_category': 'FALLBACK_REQUIRED'}
    def handoff(result, requested_action, trigger, *, request_origin='SOURCE_RECOVERABILITY', policy_binding=None):
        reference = result['operation_context']['operation_reference'] + ':action:' + str(len(result['action_decisions']))
        directive = {'requested_action': requested_action, 'trigger': trigger,
            'origin_assessment_reference': result['origin_assessment']['assessment_binding']['assessment_reference'],
            'causing_decision_reference': reference, 'evidence_references': [result['origin_assessment']['assessment_binding']['diagnosis_reference']],
            'actual_mode_status': 'NOT_ENTERED_BY_N2', 'reason': 'Declared handoff; no mode is entered by this packet.',
            'request_origin': request_origin, 'policy_binding': copy.deepcopy(policy_binding)}
        result.update(outcome='HANDOFF_REQUIRED', directive=directive)
        value = decision(result, 'HANDOFF', 'ESCALATE_TO_CONTAINMENT' if requested_action == 'ENTER_CONTAINMENT' else 'NOT_APPLICABLE', directive=directive)
        if requested_action == 'REMAIN_SAFE_HALT':
            record = result['emitted_diagnostics'][-1]; ref = record['diagnostic_reference']
            record['envelope'] = envelope(ref, None, ref, 'ash_state_' + ''.join(map(str, result['origin_assessment']['parsed_state']['bits'])),
                'CRITICAL', 'BLOCKED', ['ASH-STATE-GENERAL-001', 'ASH-RECOVERY-ACTION-001'], kind='STATE_VALIDITY', stage='DETECTION')
        return finish(result)
    packets = []
    stable = packet(origin('stable', 0)); decision(stable, 'NO_ACTION', 'NOT_APPLICABLE'); packets.append(finish(stable))
    correctable = packet(origin('correction', 480, known=True)); correctable['outcome'] = 'RECOVERED_VALUE'
    known = {'provider_source_verification': 'DECLARED_NOT_AUTHENTICATED', 'correction_reference': 'n2_authored:correction:known',
        'original_assessment_reference': correctable['origin_assessment']['assessment_binding']['assessment_reference'],
        'source_binding': provenance('n2_authored:known:source'), 'profile_id': binding['profile_id'],
        'profile_source_sha256': declared_source['source_sha256'], 'chain': [state(480)], 'expected_target': state(0),
        'reason': 'Exact source generator g1 maps declared original to neutral valid target.',
        'classification_evidence_reference': correctable['origin_assessment']['classification_evidence']['correction_path_is_known']['binding']['evidence_reference'],
        'canonical_binding': copy.deepcopy(source)}
    correctable['correction_observation'] = {'submitted': known, 'validation': {'status': 'VERIFIED', 'submitted_correction': copy.deepcopy(known),
        'origin_validation': copy.deepcopy(correctable['origin_validation']), 'current_source_binding': copy.deepcopy(source),
        'current_profile_binding': copy.deepcopy(binding), 'computed_target': state(0), 'target_diagnostic': diagnostic(0),
        'failure_code': None, 'field_name': None}}
    step(correctable, 'CORRECTION_RESOLVE', 480, 480); step(correctable, 'CORRECTION_XOR', 480, 0, codeword=480)
    post_reference = post(correctable, 0, correctable['operation_context']['operation_reference'] + ':action:0')
    step(correctable, 'POST_ASSESSMENT', 0, 0, post=post_reference)
    decision(correctable, 'CORRECT', 'RECOVERED', target=0, post=post_reference); correctable['candidate_state'] = state(0)
    packets.append(finish(correctable))
    fallback = packet(origin('fallback', 1, fallback=True)); fallback['outcome'] = 'RECOVERED_FALLBACK_VALUE'
    bind_registry(fallback, registries[0]); step(fallback, 'FALLBACK_SELECT', 1, 0)
    fallback['steps'][-1]['policy_id'] = entry['policy_id']; fallback['emitted_diagnostics'][-1]['payload']['policy_id'] = entry['policy_id']
    post_reference = post(fallback, 0, fallback['operation_context']['operation_reference'] + ':action:0')
    step(fallback, 'POST_ASSESSMENT', 0, 0, post=post_reference)
    first = decision(fallback, 'FALLBACK_CANDIDATE', 'RECOVERED_VIA_FALLBACK', target=0, policy_id=entry['policy_id'], post=post_reference)
    fallback['policy_attempts'] = [{'policy_id': entry['policy_id'], 'applicability_observations': [], 'unconsulted_applicability': [],
        'validation_observations': [], 'unconsulted_validation': [], 'post_assessment_reference': post_reference,
        'decision_reference': first['action_reference'], 'result': 'RECOVERED'}]
    decision(fallback, 'FALLBACK_SUMMARY', 'RECOVERED_VIA_FALLBACK', target=0, policy_id=entry['policy_id'], post=post_reference)
    fallback['candidate_state'] = state(0); packets.append(finish(fallback))
    failed = packet(origin('failed', 1)); packets.append(handoff(failed, 'REQUEST_EXTERNAL_AUTHORITY', {
        'trigger_domain': 'YWE_RECOVERABILITY_CATEGORY', 'recovery_category': 'ESCALATION_REQUIRED', 'authority_status': 'REACHABLE'}))
    for index, snapshot in enumerate(registries[1:]):
        empty = packet(origin('empty-registry-' + str(index), 1, fallback=True)); bind_registry(empty, snapshot)
        decision(empty, 'FALLBACK_SUMMARY', 'BLOCKED')
        packets.append(handoff(empty, 'ENTER_CONTAINMENT', 'FALLBACK_FAILURE'))
    for mode in ('CONTAINED', 'SAFE_HALT'):
        boundary = packet(origin(mode.lower(), 0, contained=mode == 'CONTAINED', halt=mode == 'SAFE_HALT'))
        packets.append(handoff(boundary, 'REMAIN_' + mode, {'trigger_domain': 'YWE_OBSERVED_MODE_BOUNDARY',
            'observed_system_state_class': mode, 'observed_assessment_reference': boundary['origin_assessment']['assessment_binding']['assessment_reference']},
            request_origin='OBSERVED_EXISTING_MODE'))
    blocked = packet(origin('normalization-unavailable', 480))
    diagnosis = copy.deepcopy(blocked['origin_assessment']); diagnosis['outcome'] = 'diagnosis'; diagnosis['emitted_diagnostics'] = diagnosis['emitted_diagnostics'][:1]
    for field in ('system_context', 'classification_evidence', 'system_state_class', 'recovery_category', 'consulted_predicates'): diagnosis.pop(field)
    normalization_policy_record = {'policy_id': 'YWE-NORMALIZE-LEXICOGRAPHIC-001', 'policy_version': '1.0.0',
        'source_reference': 'docs/architecture/m3_normalization_policy.md', 'source_sha256': N1_POLICY_PIN}
    blocked['normalization_preparation'] = {'status': 'UNAVAILABLE', 'original_diagnosis': diagnosis,
        'policy_binding': normalization_policy_record, 'plan': None, 'plan_validation': None, 'planning_error': None,
        'resolution_observation': {'availability': 'UNAVAILABLE', 'operation_reference': blocked['operation_context']['operation_reference'],
            'origin_assessment_reference': blocked['origin_assessment']['assessment_binding']['assessment_reference'],
            'source_binding': provenance('n2_authored:resolver'), 'reason': 'Typed resolution unavailability; the mathematical target set is nonempty.'}}
    decision(blocked, 'NORMALIZE', 'BLOCKED')
    packets.append(handoff(blocked, 'ENTER_CONTAINMENT', 'OPERATOR_REQUEST', request_origin='POLICY', policy_binding={
        'policy_id': 'YWE-RECOVERY-SAFETY-001', 'policy_version': '1.0.0',
        'source_path': 'docs/architecture/m3_recovery_safety_policy.md', 'source_sha256': POLICY_PIN}))
    capture = copy.deepcopy(correctable); capture.update(outcome='FAILURE', post_assessments=[], action_decisions=[], candidate_state=state(0))
    capture['steps'] = capture['steps'][:2]; capture['emitted_diagnostics'] = capture['emitted_diagnostics'][:1]
    attempted = copy.deepcopy(correctable['emitted_diagnostics'][1])
    capture['failure_detail'] = {'failure_code': 'STEP_CAPTURE_REJECTED', 'field_name': 'capture.append', 'submitted_evidence': None,
        'attempted_diagnostic': attempted, 'capture_status': 'REJECTED', 'pending_directive': None,
        'reason': 'Declared XOR value exists while its immediate capture was rejected.',
        'completion_failure_code': 'COMPLETION_REJECTED', 'unconfirmed_completion_observation': None}
    capture['completion_observation'] = completion(capture['operation_context']['operation_reference'], 1, incomplete=True)
    packets.append(capture)
    completion_failed = copy.deepcopy(correctable); completion_failed['outcome'] = 'FAILURE'
    completion_failed['completion_observation'] = completion(completion_failed['operation_context']['operation_reference'], len(completion_failed['emitted_diagnostics']), incomplete=True)
    completion_failed['failure_detail'] = {'failure_code': 'COMPLETION_REJECTED', 'field_name': 'capture.finish',
        'submitted_evidence': copy.deepcopy(completion_failed['completion_observation']), 'attempted_diagnostic': None,
        'capture_status': 'REJECTED', 'pending_directive': None, 'reason': 'Retained complete value evidence is not published as recovery success.',
        'completion_failure_code': 'COMPLETION_REJECTED', 'unconfirmed_completion_observation': None}
    packets.append(completion_failed)
    normalized = packet(origin('normalization-ready', 480)); normalized['outcome'] = 'RECOVERED_VALUE'
    diagnosis = copy.deepcopy(normalized['origin_assessment']); diagnosis['outcome'] = 'diagnosis'; diagnosis['emitted_diagnostics'] = diagnosis['emitted_diagnostics'][:1]
    for field in ('system_context', 'classification_evidence', 'system_state_class', 'recovery_category', 'consulted_predicates'): diagnosis.pop(field)
    plan = {'schema_ref': 'data/schemas/m3_normalization_plan_schema.json', 'artifact_type': 'ywe_state_normalization_plan',
        'artifact_version': '1.0.0', 'plan_reference': 'n2_authored:normalization:plan',
        'evidence_reference': 'n2_authored:normalization:proof', 'policy_binding': copy.deepcopy(normalization_policy_record),
        'original_diagnosis': diagnosis, 'decision': 'PLAN_READY', 'eligible_targets_complete': True,
        'eligible_targets': [state(0)], 'selected_target': state(0), 'codeword_chain': [state(480)], 'reason_code': 'NORMALIZATION_PLAN_READY'}
    normalized['normalization_preparation'] = {'status': 'READY', 'original_diagnosis': copy.deepcopy(diagnosis),
        'policy_binding': copy.deepcopy(normalization_policy_record), 'plan': plan,
        'plan_validation': {'plan': copy.deepcopy(plan), 'original_diagnosis': copy.deepcopy(diagnosis),
            'canonical_binding': copy.deepcopy(source), 'profile_binding': copy.deepcopy(binding),
            'origin_validation_status': 'VERIFIED', 'validation_status': 'VALIDATED', 'failure_code': None, 'field_name': None,
            'expected_decision': 'PLAN_READY', 'recomputed_eligible_targets': [state(0)], 'recomputed_target': state(0),
            'recomputed_codeword_chain': [state(480)]}, 'planning_error': None,
        'resolution_observation': {'availability': 'READY', 'operation_reference': normalized['operation_context']['operation_reference'],
            'origin_assessment_reference': normalized['origin_assessment']['assessment_binding']['assessment_reference'],
            'source_binding': provenance('n2_authored:resolver'), 'reason': 'Complete current-model proof is explicitly declared.'}}
    step(normalized, 'NORMALIZE_PLAN', 480, 480); step(normalized, 'NORMALIZE_XOR', 480, 0, codeword=480)
    post_reference = post(normalized, 0, normalized['operation_context']['operation_reference'] + ':action:0')
    step(normalized, 'POST_ASSESSMENT', 0, 0, post=post_reference)
    decision(normalized, 'NORMALIZE', 'RECOVERED', target=0, post=post_reference); normalized['candidate_state'] = state(0)
    packets.append(finish(normalized))
    after_correction = packet(origin('after-correction-unavailable', 480, known=True))
    origin_fact = after_correction['origin_assessment']['classification_evidence']['correction_path_is_known']['binding']['evidence_reference']
    after_correction['correction_observation'] = {'submitted': {'provider_source_verification': 'DECLARED_NOT_AUTHENTICATED',
        'original_assessment_reference': after_correction['origin_assessment']['assessment_binding']['assessment_reference'],
        'source_binding': provenance('n2_authored:known:unavailable'), 'reason': 'Declared known-path provider is unavailable.',
        'classification_evidence_reference': origin_fact}, 'validation': None}
    step(after_correction, 'CORRECTION_RESOLVE', 480, 480)
    after_correction['steps'][-1]['status'] = 'BLOCKED'; after_correction['emitted_diagnostics'][-1]['payload']['status'] = 'BLOCKED'
    after_correction['emitted_diagnostics'][-1]['envelope']['disposition'] = 'BLOCKED'
    correction_decision = decision(after_correction, 'CORRECT', 'BLOCKED')
    bind_registry(after_correction, registries[0])
    after_correction['route_authorization'].update(route='AFTER_CORRECTION_FAILURE', original_system_state_class='CORRECTABLE',
        failed_action_decision_reference=correction_decision['action_reference'], failed_outcome='BLOCKED',
        origin_predicate_evidence_reference=origin_fact)
    step(after_correction, 'FALLBACK_SELECT', 480, 0)
    after_correction['steps'][-1]['policy_id'] = entry['policy_id']; after_correction['emitted_diagnostics'][-1]['payload']['policy_id'] = entry['policy_id']
    post_reference = post(after_correction, 0, after_correction['operation_context']['operation_reference'] + ':action:1')
    step(after_correction, 'POST_ASSESSMENT', 0, 0, post=post_reference)
    first = decision(after_correction, 'FALLBACK_CANDIDATE', 'RECOVERED_VIA_FALLBACK', target=0, policy_id=entry['policy_id'], post=post_reference)
    after_correction['policy_attempts'] = [{'policy_id': entry['policy_id'], 'applicability_observations': [], 'unconsulted_applicability': [],
        'validation_observations': [], 'unconsulted_validation': [], 'post_assessment_reference': post_reference,
        'decision_reference': first['action_reference'], 'result': 'RECOVERED'}]
    decision(after_correction, 'FALLBACK_SUMMARY', 'RECOVERED_VIA_FALLBACK', target=0, policy_id=entry['policy_id'], post=post_reference)
    after_correction.update(outcome='RECOVERED_FALLBACK_VALUE', candidate_state=state(0)); packets.append(finish(after_correction))
    return packets, registries


class RecoveryIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.generators, self.words = source_codewords()
        self.g1, self.g2 = self.generators[:2]

    def fixture(self, *, states=(0,), original=None, known=False, fallback=False, halt=False, contained=False,
                entries=(), diagnostics=None, correction=None, norm='READY', post=None, conditions=None,
                registry_unavailable=False, canonical=None):
        diagnostics = ControlledDiagnostics() if diagnostics is None else diagnostics
        binding = profile(states)
        model = StateModel(binding, canonical_binding() if canonical is None else canonical,
                           diagnostics.assessment_capture())
        origin = assessment(model, ash(self.g1 if original is None else original), known=known,
                            fallback=fallback, halt=halt, contained=contained)
        actual_registry = registry(model, entries, unavailable=registry_unavailable)
        correction_provider = CorrectionProvider(correction)
        resolver = NormalizationResolver(model, norm)
        evaluator = Conditions() if conditions is None else conditions
        post_provider = PostFacts(binding) if post is None else post
        engine = RecoveryEngine(model, actual_registry, diagnostics, resolver, correction_provider,
                                evaluator, post_provider)
        return model, origin, engine, diagnostics, resolver, correction_provider, evaluator, post_provider

    def assert_no_value_effects(self, result, *, posts=0):
        self.assertFalse(result.session_effects_performed)
        self.assertEqual(len(result.post_assessments), posts)
        self.assertEqual([s for s in result.steps if s.action in ('NORMALIZE_XOR', 'CORRECTION_XOR')], [])

    def assert_chain(self, result):
        records = result.emitted_diagnostics
        for first, second in zip(records, records[1:]):
            self.assertEqual(second.envelope.parent_diagnostic_reference, first.diagnostic_reference)
            self.assertGreaterEqual(SEVERITY[second.envelope.severity], SEVERITY[first.envelope.severity])
        for action in result.action_decisions:
            self.assertEqual(action.diagnostic.recovery_category, result.origin_assessment.recovery_category)
            self.assertEqual(action.diagnostic.original_state_class, result.origin_assessment.system_state_class)
            self.assertEqual(action.diagnostic.original_diagnostic, result.origin_assessment.state_validity_diagnostic)
            self.assertLessEqual(len(action.diagnostic.steps), 32)
        for linked in result.post_assessments:
            self.assertEqual(linked.assessment.source_binding, result.origin_assessment.source_binding)
            self.assertEqual(linked.assessment.profile_binding, result.origin_assessment.profile_binding)
            self.assertEqual(linked.assessment.emitted_diagnostics[0].envelope.parent_diagnostic_reference, None)
            self.assertNotEqual(linked.assessment.emitted_diagnostics[0].diagnostic_reference,
                                result.origin_assessment.emitted_diagnostics[0].diagnostic_reference)

    def test_pinned_sources_and_independent_two_codeword_oracle(self):
        self.assertEqual(normalized_hash(CANONICAL / 'core/codeword-set.pseudo.md'), CODEWORD_PIN)
        self.assertEqual(normalized_hash(ROOT / 'docs/architecture/m3_recovery_safety_policy.md'), POLICY_PIN)
        fingerprint = hashlib.sha256()
        for original, first, second in itertools.product(range(512), self.words, self.words):
            row = [original, first, original ^ first, second, original ^ first ^ second]
            fingerprint.update((json.dumps(row, separators=(',', ':')) + '\n').encode('ascii'))
        self.assertEqual(fingerprint.hexdigest(), MATH_PIN)

    def test_pure_inspection_all512_and_actual_correction_proofs_all_two_member_paths(self):
        binding = profile(range(512))
        class NoCapture:
            def begin(self, *_args, **_kwargs):
                raise AssertionError('Pure validation must not capture')
        model = StateModel(binding, canonical_binding(), NoCapture())
        originating_model = StateModel(binding, canonical_binding(), RecordingDiagnosticCapture())
        for original in range(512):
            with self.subTest(original=original):
                diagnostic = model.inspect_state(ash(original))
                self.assertEqual(diagnostic.admissibility_status, 'VALID')
                self.assertEqual(diagnostic.orbit_info.orbit_id, format(min(original ^ word for word in self.words), '09b'))
                origin = assessment(originating_model, ash(original), reference=f'n2:math:{original}', known=True)
                self.assertEqual(model.validate_assessment(origin).status, 'VERIFIED')
                for first, second in itertools.product(self.words, repeat=2):
                    target = original ^ first ^ second
                    proof = model.validate_known_correction(known_correction(origin, (first, second), target), origin=origin)
                    self.assertEqual(proof.status, 'VERIFIED')
                    self.assertEqual(number(proof.computed_target), target)
                    self.assertEqual(proof.target_diagnostic.admissibility_status, 'VALID')

    def test_full64_actual_assessment_classification_and_pure_validation(self):
        configurations = [('VALID', (0,), 0), ('TRANSFORMATION_COMPATIBLE', (0,), self.g1),
                          ('TRANSFORMATION_INCOMPATIBLE', (0,), 1), ('UNCLASSIFIED', None, 0)]
        for semantic, states, state in configurations:
            source = sv.ProfileSourceBinding('n2:unavailable:source', 'a' * 64, 'n2:unavailable:evidence')
            binding = (sv.UnavailableProfileBinding(sv.UnavailableValidityProfileEvidence(
                           'n2:unavailable', source, 'PROFILE_DATA_UNAVAILABLE', 'Declared unavailable.'))
                       if states is None else profile(states))
            model = StateModel(binding, canonical_binding(), RecordingDiagnosticCapture())
            for halt, contained, known, fallback in itertools.product((False, True), repeat=4):
                with self.subTest(row=semantic, flags=(halt, contained, known, fallback)):
                    expected = ('SAFE_HALT' if halt else 'CONTAINED' if contained else 'STABLE' if semantic == 'VALID'
                                else ('CORRECTABLE' if known else 'UNSTABLE') if semantic == 'TRANSFORMATION_COMPATIBLE'
                                else ('DEGRADED' if fallback else 'FAILED') if semantic == 'TRANSFORMATION_INCOMPATIBLE'
                                else 'DEGRADED')
                    value = assessment(model, ash(state), known=known, fallback=fallback, halt=halt, contained=contained)
                    validation = model.validate_assessment(value)
                    self.assertEqual(value.system_state_class, expected)
                    self.assertEqual(value.recovery_category, CATEGORIES[expected])
                    self.assertEqual(validation.status, 'VERIFIED')
                    self.assertEqual(validation.expected_system_state_class, expected)
                    self.assertEqual(validation.expected_recovery_category, CATEGORIES[expected])
                    self.assertEqual(tuple(validation.expected_diagnostic.rule_ids), DIAGNOSIS_RULES)

    def test_pure_validation_rejects_foreign_full_profile_with_same_id_and_digest(self):
        source = sv.ProfileSourceBinding('n2:same:source', 'a' * 64, 'n2:same:evidence')
        model = StateModel(profile((0,), source=source), canonical_binding(), RecordingDiagnosticCapture())
        foreign = StateModel(profile((0, self.g2), source=source), canonical_binding(), RecordingDiagnosticCapture())
        submitted = assessment(foreign, ash(0))
        value = model.validate_assessment(submitted)
        self.assertEqual(value.status, 'REJECTED')
        self.assertEqual(value.failure_code, 'PROFILE_BINDING_MISMATCH')
        self.assertEqual(value.submitted_assessment, submitted)
        self.assertEqual(value.current_profile_binding, model.profile_binding)
        self.assertNotEqual(value.current_profile_binding, submitted.profile_binding)
        projection = model.diagnosis_from_assessment(submitted)
        self.assertEqual(projection, value)

    def test_pure_validation_rejects_controlled_forged_math_class_predicates_and_envelopes(self):
        model, origin, *_ = self.fixture(original=0)
        envelope = origin.emitted_diagnostics[1].envelope
        bad_predicate = dataclasses.replace(origin.classification_evidence.fallback_is_available.binding,
                                             subject_reference='ash_state_111111111')
        changes = [
            ('CLASSIFICATION_MISMATCH', reflectively_forged(origin, system_state_class='DEGRADED',
                                                            recovery_category='FALLBACK_REQUIRED')),
            ('DIAGNOSIS_MISMATCH', reflectively_forged(origin, state_validity_diagnostic=reflectively_forged(
                origin.state_validity_diagnostic, normalization_status='NORMALIZABLE'))),
            ('DIAGNOSIS_MISMATCH', reflectively_forged(origin, state_validity_diagnostic=reflectively_forged(
                origin.state_validity_diagnostic, rule_ids=tuple(reversed(DIAGNOSIS_RULES))))),
            ('PREDICATE_BINDING_MISMATCH', reflectively_forged(origin, classification_evidence=dataclasses.replace(
                origin.classification_evidence, fallback_is_available=sv.EvaluatedPredicate(bad_predicate, False)))),
            ('CLASSIFICATION_ENVELOPE_MISMATCH', reflectively_forged(origin, emitted_diagnostics=(
                origin.emitted_diagnostics[0], sv.DiagnosticEmission(origin.emitted_diagnostics[1].diagnostic_reference,
                                                                     dataclasses.replace(envelope, disposition='BLOCKED'))))),
        ]
        for code, submitted in changes:
            with self.subTest(code=code):
                value = model.validate_assessment(submitted)
                self.assertEqual(value.status, 'REJECTED')
                self.assertEqual(value.failure_code, code)
                self.assertEqual(value.submitted_assessment, submitted)

    def test_pure_diagnosis_projection_preserves_actual_owned_prefix_without_capture(self):
        model, origin, _, diagnostics, *_ = self.fixture()
        calls = list(diagnostics.calls)
        diagnosis = model.diagnosis_from_assessment(origin)
        self.assertEqual(diagnostics.calls, calls)
        self.assertIs(type(diagnosis), sv.StateDiagnosis)
        self.assertEqual(diagnosis.emitted_diagnostics, origin.emitted_diagnostics[:1])
        self.assertEqual(diagnosis.input_evidence, origin.input_evidence)
        self.assertEqual(diagnosis.state_validity_diagnostic, origin.state_validity_diagnostic)
        self.assertEqual(diagnosis.parsed_state, origin.parsed_state)

    def test_all_seven_category_routes_use_actual_coherent_origins(self):
        cases = [('STABLE', 0, False, False, False, False, 'NO_ACTION', None),
                 ('UNSTABLE', self.g1, False, False, False, False, 'RECOVERED_VALUE', None),
                 ('CORRECTABLE', self.g1, True, False, False, False, 'HANDOFF_REQUIRED', 'ENTER_CONTAINMENT'),
                 ('DEGRADED', 1, False, True, False, False, 'HANDOFF_REQUIRED', 'ENTER_CONTAINMENT'),
                 ('CONTAINED', 0, False, False, False, True, 'HANDOFF_REQUIRED', 'REMAIN_CONTAINED'),
                 ('FAILED', 1, False, False, False, False, 'HANDOFF_REQUIRED', 'REQUEST_EXTERNAL_AUTHORITY'),
                 ('SAFE_HALT', 0, False, False, True, False, 'HANDOFF_REQUIRED', 'REMAIN_SAFE_HALT')]
        for expected, original, known, fallback, halt, contained, outcome, directive in cases:
            with self.subTest(expected=expected):
                model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture(
                    original=original, known=known, fallback=fallback, halt=halt, contained=contained)
                frozen = origin.to_record()
                result = engine.recover(origin, operation_context=operation(origin))
                self.assertEqual(origin.system_state_class, expected)
                self.assertEqual(result.outcome, outcome)
                self.assertEqual(result.origin_assessment.to_record(), frozen)
                self.assertEqual(origin.to_record(), frozen)
                self.assertFalse(result.session_effects_performed)
                self.assertEqual(result.completion_observation.status, 'COMPLETE')
                if directive:
                    self.assertEqual(result.directive.requested_action, directive)
                    self.assertEqual(result.directive.actual_mode_status, 'NOT_ENTERED_BY_N2')
                    self.assertEqual(result.action_decisions[-1].diagnostic.outcome,
                                     'ESCALATE_TO_CONTAINMENT' if directive == 'ENTER_CONTAINMENT' else 'NOT_APPLICABLE')
                if expected in ('CONTAINED', 'FAILED', 'SAFE_HALT', 'STABLE'):
                    self.assertEqual(provider.calls, [])
                    self.assertEqual(resolver.calls, [])
                    self.assertEqual(evaluator.calls, [])
                    self.assertEqual(post.calls, [])
                if expected == 'SAFE_HALT':
                    self.assertEqual([row.envelope.stage for row in result.emitted_diagnostics], ['DETECTION'])
                    self.assertIsNone(result.emitted_diagnostics[0].envelope.parent_diagnostic_reference)
                else:
                    self.assert_chain(result)

    def test_known_sequence_is_replayed_without_normalizer_substitution(self):
        cases = [(self.g1,), (self.g2, self.g1 ^ self.g2), (self.g2, self.g2, self.g1),
                 (0, self.g1), (0,) * 15 + (self.g1,)]
        for chain in cases:
            with self.subTest(chain=chain):
                model, origin, engine, diagnostics, resolver, provider, *_ = self.fixture(known=True)
                provider.result = known_correction(origin, chain, 0)
                result = engine.recover(origin, operation_context=operation(origin))
                self.assertEqual(result.outcome, 'RECOVERED_VALUE')
                self.assertEqual(resolver.calls, [])
                actual = [step for step in result.steps if step.action == 'CORRECTION_XOR']
                self.assertEqual(len(actual), len(chain))
                before = self.g1
                for step, word in zip(actual, chain):
                    self.assertEqual((number(step.before_state), number(step.codeword), number(step.after_state)),
                                     (before, word, before ^ word))
                    before ^= word
                self.assertEqual(number(result.candidate_state), 0)
                self.assertEqual(result.correction_observation.submitted.chain, tuple(ash(word) for word in chain))
                self.assertEqual(result.correction_observation.validation.status, 'VERIFIED')
                self.assert_chain(result)
        model, origin, engine, diagnostics, resolver, provider, *_ = self.fixture(states=(0, self.g2), known=True)
        provider.result = known_correction(origin, (self.g1 ^ self.g2,), self.g2)
        result = engine.recover(origin, operation_context=operation(origin))
        self.assertEqual(number(result.candidate_state), self.g2)
        self.assertEqual(resolver.calls, [])

    def test_known_bad_proofs_are_rejected_before_replay_and_take_authorized_fallback(self):
        cases = [((0,), self.g1, 'TARGET_NOT_VALID'), ((), self.g1, 'TARGET_NOT_VALID'),
                 ((self.g1, self.g1), self.g1, 'TARGET_NOT_VALID'),
                 ((self.g1,), self.g2, 'CHAIN_TARGET_MISMATCH'),
                 ((1,), self.g1 ^ 1, 'CHAIN_MEMBER_INVALID'),
                 ((self.g1 ^ self.g2,), self.g2, 'TARGET_NOT_VALID')]
        for chain, target, expected in cases:
            with self.subTest(chain=chain, target=target):
                model, origin, engine, diagnostics, resolver, provider, *_ = self.fixture(known=True)
                provider.result = known_correction(origin, chain, target)
                pure = model.validate_known_correction(provider.result, origin=origin)
                self.assertEqual(pure.status, 'REJECTED')
                self.assertEqual(pure.failure_code, expected)
                result = engine.recover(origin, operation_context=operation(origin))
                self.assertEqual(result.outcome, 'HANDOFF_REQUIRED')
                self.assert_no_value_effects(result)
                self.assertEqual(result.route_authorization.route, 'AFTER_CORRECTION_FAILURE')
                self.assertEqual(result.route_authorization.original_system_state_class, 'CORRECTABLE')
                self.assertEqual(result.correction_observation.validation, pure)
                self.assertEqual(resolver.calls, [])
                self.assert_chain(result)

    def test_available_empty_profile_cannot_fabricate_a_correctable_origin(self):
        model, origin, engine, *_ = self.fixture(states=(), known=True)
        self.assertEqual(origin.system_state_class, 'FAILED')
        submitted = known_correction(origin, (self.g1,), 0)
        proof = model.validate_known_correction(submitted, origin=origin)
        self.assertEqual(proof.status, 'REJECTED')
        self.assertEqual(proof.failure_code, 'TARGET_NOT_VALID')
        self.assertEqual(proof.target_diagnostic.admissibility_status, 'TRANSFORMATION_INCOMPATIBLE')

    def test_owned_known_path_seventeen_bound_refuses_before_provider_call(self):
        model, origin, engine, diagnostics, resolver, provider, *_ = self.fixture(known=True)
        with self.assertRaises(rv.RecoveryContractError):
            known_correction(origin, (0,) * 16 + (self.g1,), 0)
        self.assertEqual(provider.calls, [])
        self.assertEqual(resolver.calls, [])
        self.assertEqual(diagnostics.records, [])

    def test_normalization_resolution_ready_unavailable_and_collaborator_failures(self):
        for mode in ('READY', 'UNAVAILABLE', 'NONE', 'THROW', 'BAD_PROOF'):
            with self.subTest(mode=mode):
                model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture(norm=mode)
                result = engine.recover(origin, operation_context=operation(origin))
                if mode == 'READY':
                    self.assertEqual(result.outcome, 'RECOVERED_VALUE')
                    self.assertEqual(number(result.candidate_state), 0)
                    self.assertEqual(result.normalization_preparation.plan.decision, 'PLAN_READY')
                    self.assertEqual(tuple(number(s) for s in result.normalization_preparation.plan.eligible_targets), (0,))
                elif mode == 'UNAVAILABLE':
                    self.assertEqual(result.outcome, 'HANDOFF_REQUIRED')
                    self.assertEqual(result.directive.requested_action, 'ENTER_CONTAINMENT')
                    self.assertEqual(result.directive.trigger, 'OPERATOR_REQUEST')
                    self.assertEqual(result.directive.request_origin, 'POLICY')
                    self.assertEqual(result.directive.policy_binding.source_sha256, POLICY_PIN)
                    self.assertIsNone(result.route_authorization)
                    self.assertEqual(result.normalization_preparation.resolution_observation.availability, 'UNAVAILABLE')
                    self.assert_no_value_effects(result)
                else:
                    self.assertEqual(result.outcome, 'FAILURE')
                    self.assertEqual(result.failure_detail.failure_code, 'COLLABORATOR_FAILED')
                    self.assert_no_value_effects(result)
                    self.assertIsNone(result.directive)
                self.assertEqual(provider.calls, [])
                self.assertEqual(evaluator.calls, [])

    def test_128_reachable_three_entry_fallback_control_combinations(self):
        for origin_class in ('DEGRADED', 'CORRECTABLE'):
            for statuses in itertools.product(range(4), repeat=3):
                with self.subTest(origin_class=origin_class, statuses=statuses):
                    entries, observations = entries_for(statuses)
                    evaluator = Conditions(observations)
                    model, origin, engine, diagnostics, resolver, provider, _, post = self.fixture(
                        original=1 if origin_class == 'DEGRADED' else self.g1,
                        known=origin_class == 'CORRECTABLE', fallback=origin_class == 'DEGRADED',
                        entries=entries, conditions=evaluator)
                    attempted, selected = [], None
                    for index, status in enumerate(statuses):
                        if status == 0:
                            continue
                        attempted.append(f'FALLBACK-STATE-{index + 1:03d}')
                        if status == 1:
                            selected = attempted[-1]
                            break
                        if status == 3:
                            break
                    result = engine.recover(origin, operation_context=operation(origin))
                    self.assertEqual(result.origin_assessment.system_state_class, origin_class)
                    self.assertEqual([call[0] for call in evaluator.calls if call[1] == 'ADDITIONAL_VALIDATION'], attempted)
                    self.assertEqual(len(post.calls), len(attempted))
                    if selected:
                        self.assertEqual(result.outcome, 'RECOVERED_FALLBACK_VALUE')
                        recovered = [a for a in result.action_decisions if a.diagnostic.outcome == 'RECOVERED_VIA_FALLBACK']
                        self.assertTrue(recovered)
                        self.assertEqual(recovered[-1].diagnostic.fallback_policy_id, selected)
                    else:
                        self.assertEqual(result.outcome, 'HANDOFF_REQUIRED')
                        self.assertEqual(result.directive.requested_action, 'ENTER_CONTAINMENT')
                    self.assertEqual(result.route_authorization.route,
                                     'DIRECT_DEGRADED' if origin_class == 'DEGRADED' else 'AFTER_CORRECTION_FAILURE')
                    self.assert_chain(result)
                    self.assertEqual(resolver.calls, [])

    def test_registry_unavailable_and_available_empty_have_distinct_retained_evidence(self):
        for unavailable in (False, True):
            model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture(
                original=1, fallback=True, registry_unavailable=unavailable)
            result = engine.recover(origin, operation_context=operation(origin))
            self.assertEqual(result.outcome, 'HANDOFF_REQUIRED')
            self.assertEqual(result.registry_snapshot.availability, 'UNAVAILABLE' if unavailable else 'AVAILABLE')
            self.assertEqual(result.directive.requested_action, 'ENTER_CONTAINMENT')
            self.assertEqual(evaluator.calls, [])
            self.assertEqual(post.calls, [])
            self.assert_no_value_effects(result)

    def test_propagation_and_external_authority_boundaries_before_value_effects(self):
        for status in ('RISK', 'UNAVAILABLE'):
            for known in (False, True):
                model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture(known=known)
                result = engine.recover(origin, operation_context=operation(origin, propagation=status))
                self.assertEqual(result.outcome, 'HANDOFF_REQUIRED')
                self.assertEqual(result.directive.requested_action, 'ENTER_CONTAINMENT')
                self.assert_no_value_effects(result)
                self.assertEqual(provider.calls, [])
                self.assertEqual(resolver.calls, [])
        for status, action in [('REACHABLE', 'REQUEST_EXTERNAL_AUTHORITY'),
                               ('UNREACHABLE', 'ENTER_SAFE_HALT'), ('UNAVAILABLE', 'REQUEST_EXTERNAL_AUTHORITY')]:
            model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture(original=1)
            result = engine.recover(origin, operation_context=operation(origin, authority=status))
            self.assertEqual(result.directive.requested_action, action)
            self.assertEqual(result.origin_assessment.system_state_class, 'FAILED')
            self.assertEqual(result.action_decisions[-1].diagnostic.outcome, 'NOT_APPLICABLE')
            self.assertIsNone(result.route_authorization)
            self.assert_no_value_effects(result)

    def test_valid_contextual_containment_and_halt_stop_all_later_candidates(self):
        entries, observations = entries_for((2, 1, 1))
        for halt, contained, action in [(False, True, 'REMAIN_CONTAINED'),
                                         (True, False, 'REMAIN_SAFE_HALT'), (True, True, 'REMAIN_SAFE_HALT')]:
            with self.subTest(halt=halt, contained=contained):
                binding = profile()
                post = PostFacts(binding, halt=halt, contained=contained)
                model, origin, engine, diagnostics, resolver, provider, evaluator, _ = self.fixture(
                    original=1, fallback=True, entries=entries, conditions=Conditions(observations), post=post)
                result = engine.recover(origin, operation_context=operation(origin))
                self.assertEqual(result.outcome, 'HANDOFF_REQUIRED')
                self.assertEqual(result.directive.requested_action, action)
                self.assertEqual(result.action_decisions[-1].diagnostic.outcome, 'NOT_APPLICABLE')
                self.assertEqual(len(post.calls), 1)
                self.assertEqual(result.post_assessments[0].assessment.state_validity_diagnostic.admissibility_status, 'VALID')
                self.assertEqual(result.post_assessments[0].assessment.system_context, sv.SystemContext(halt, contained))
                self.assertEqual([call for call in evaluator.calls if call[1] == 'ADDITIONAL_VALIDATION'], [])

    def test_capture_admission_refusals_execute_no_collaborator_or_value_action(self):
        for mode in ('REJECTED', 'NOT_CONFIRMED', 'THROW', 'NONE', 'BAD_SCOPE'):
            diagnostics = ControlledDiagnostics(admission=mode)
            model, origin, engine, _, resolver, provider, evaluator, post = self.fixture(diagnostics=diagnostics)
            result = engine.recover(origin, operation_context=operation(origin))
            self.assertEqual(result.outcome, 'FAILURE')
            self.assertEqual(result.failure_detail.failure_code,
                             'CAPTURE_ADMISSION_REJECTED' if mode == 'REJECTED' else 'CAPTURE_ADMISSION_UNCONFIRMED')
            self.assert_no_value_effects(result)
            self.assertEqual(provider.calls, [])
            self.assertEqual(resolver.calls, [])
            self.assertEqual(evaluator.calls, [])
            self.assertEqual(post.calls, [])
            self.assertEqual(diagnostics.records, [])

    def test_18_immediate_two_xor_and_completed_action_capture_boundaries(self):
        for stage in range(3):
            for mode in ('THROW_BEFORE', 'THROW_AFTER', 'REJECTED', 'NOT_CONFIRMED', 'WRONG_REFERENCE', 'NONE'):
                with self.subTest(stage=stage, mode=mode):
                    seen = []
                    def selected(record):
                        relevant = (record.record_kind == 'ACTION_VALUE_COMPUTED' and record.payload.action == 'CORRECTION_XOR'
                                    or record.record_kind == 'OPERATION_DECISION' and record.payload.action == 'CORRECT')
                        if relevant:
                            seen.append(record)
                        return relevant and len(seen) == stage + 1
                    diagnostics = ControlledDiagnostics(fail=selected, mode=mode)
                    model, origin, engine, _, resolver, provider, evaluator, post = self.fixture(known=True, diagnostics=diagnostics)
                    provider.result = known_correction(origin, (self.g2, self.g1 ^ self.g2), 0)
                    result = engine.recover(origin, operation_context=operation(origin))
                    self.assertEqual(result.outcome, 'FAILURE')
                    self.assertEqual(result.failure_detail.failure_code,
                                     'STEP_CAPTURE_REJECTED' if mode == 'REJECTED' else 'STEP_CAPTURE_UNCONFIRMED')
                    self.assertEqual(result.failure_detail.attempted_diagnostic, diagnostics.failed_record)
                    self.assertEqual(len([s for s in result.steps if s.action == 'CORRECTION_XOR']), min(stage + 1, 2))
                    relevant_confirmed = [r for r in result.emitted_diagnostics if r in seen]
                    self.assertEqual(len(relevant_confirmed), stage)
                    self.assertEqual(list(result.emitted_diagnostics), diagnostics.records)
                    self.assertEqual(evaluator.calls, [])
                    self.assertEqual(len(provider.calls), 1)
                    if mode == 'THROW_AFTER':
                        self.assertIn(diagnostics.failed_record, diagnostics.private_records)
                        self.assertNotIn(diagnostics.failed_record, result.emitted_diagnostics)
                    self.assertEqual(len(diagnostics.finish_inputs), 1)

    def test_post_capture_failure_stops_later_candidates(self):
        entries, values = entries_for((2, 1, 1))
        diagnostics = ControlledDiagnostics(post_capture='REJECTED')
        model, origin, engine, _, resolver, provider, evaluator, post = self.fixture(
            original=1, fallback=True, entries=entries, conditions=Conditions(values), diagnostics=diagnostics)
        result = engine.recover(origin, operation_context=operation(origin))
        self.assertEqual(result.outcome, 'FAILURE')
        self.assertEqual(result.failure_detail.failure_code, 'POST_CAPTURE_REJECTED')
        self.assertEqual(len(post.calls), 1)
        self.assertEqual(len(result.post_assessments), 1)
        self.assertIs(type(result.post_assessments[0].assessment), sv.DiagnosticCaptureFailure)
        self.assertEqual([c for c in evaluator.calls if c[1] == 'ADDITIONAL_VALIDATION'], [])

    def test_completion_failure_preserves_primary_capture_failure_and_pending_evidence(self):
        for completion in ('INCOMPLETE', 'WRONG_REFERENCE', 'NONE', 'THROW'):
            diagnostics = ControlledDiagnostics(fail=lambda r: True, mode='REJECTED', completion=completion)
            model, origin, engine, _, resolver, provider, evaluator, post = self.fixture(diagnostics=diagnostics)
            result = engine.recover(origin, operation_context=operation(origin))
            tentative = diagnostics.finish_inputs[0]
            self.assertEqual(result.outcome, 'FAILURE')
            self.assertEqual(result.failure_detail.failure_code, 'STEP_CAPTURE_REJECTED')
            for field in ('failure_code', 'field_name', 'submitted_evidence', 'attempted_diagnostic',
                          'capture_status', 'pending_directive', 'reason'):
                self.assertEqual(getattr(result.failure_detail, field), getattr(tentative.failure_detail, field))
            self.assertEqual(result.failure_detail.completion_failure_code,
                             'COMPLETION_REJECTED' if completion == 'INCOMPLETE' else 'COMPLETION_UNCONFIRMED')
            self.assertEqual(len(diagnostics.finish_inputs), 1)
            if completion == 'INCOMPLETE':
                self.assertEqual(result.completion_observation.status, 'INCOMPLETE')
            else:
                self.assertIsNone(result.completion_observation)
            if completion == 'WRONG_REFERENCE':
                self.assertEqual(result.failure_detail.unconfirmed_completion_observation.operation_reference,
                                 'n2:operation:wrong')

    def test_success_never_published_after_bad_completion(self):
        for completion in ('INCOMPLETE', 'WRONG_REFERENCE', 'NONE', 'THROW'):
            diagnostics = ControlledDiagnostics(completion=completion)
            model, origin, engine, _, resolver, provider, evaluator, post = self.fixture(diagnostics=diagnostics)
            result = engine.recover(origin, operation_context=operation(origin))
            self.assertEqual(result.outcome, 'FAILURE')
            self.assertEqual(result.failure_detail.failure_code,
                             'COMPLETION_REJECTED' if completion == 'INCOMPLETE' else 'COMPLETION_UNCONFIRMED')
            self.assertEqual(number(result.candidate_state), 0)
            self.assertEqual(len(diagnostics.finish_inputs), 1)
            self.assertEqual(diagnostics.finish_inputs[0].outcome, 'RECOVERED_VALUE')
            self.assertIsNone(diagnostics.finish_inputs[0].completion_observation)

    def test_pure_validation_recomputes_each_seven_field_and_ordered_rule_owner(self):
        model, origin, *_ = self.fixture(original=0)
        mutations = {
            'input_state': ash(self.g2), 'admissibility_status': 'TRANSFORMATION_COMPATIBLE',
            'transformation_compatibility': 'INCOMPATIBLE', 'normalization_status': 'NORMALIZABLE',
            'recoverability_relevance': 'RECOVERY_APPLICABLE', 'is_valid': False,
            'orbit_info': sv.OrbitInfo('000000001', 16, True),
            'rule_ids': DIAGNOSIS_RULES[:-1],
        }
        for field, replacement in mutations.items():
            with self.subTest(field=field):
                submitted = reflectively_forged(origin, state_validity_diagnostic=reflectively_forged(
                    origin.state_validity_diagnostic, **{field: replacement}))
                validation = model.validate_assessment(submitted)
                self.assertEqual(validation.status, 'REJECTED')
                self.assertEqual(validation.failure_code, 'DIAGNOSIS_MISMATCH')
                self.assertEqual(validation.field_name, 'origin_assessment.state_validity_diagnostic.' + field)
                self.assertEqual(validation.expected_diagnostic, origin.state_validity_diagnostic)

    def test_pure_validation_checks_both_consulted_and_unconsulted_fact_bindings(self):
        model, origin, *_ = self.fixture(known=True)
        replacements = {'assessment_reference': 'foreign:assessment', 'diagnosis_reference': 'foreign:diagnosis',
                        'subject_reference': 'ash_state_111111111', 'profile_id': 'foreign:profile',
                        'profile_source_sha256': 'f' * 64, 'ash_dependency_id': 'foreign:dependency',
                        'ash_aggregate_sha256': 'f' * 64}
        for name in sv.PREDICATE_NAMES:
            for field, replacement in replacements.items():
                with self.subTest(predicate=name, field=field):
                    fact = getattr(origin.classification_evidence, name)
                    bad = dataclasses.replace(fact, binding=dataclasses.replace(fact.binding, **{field: replacement}))
                    submitted = reflectively_forged(origin, classification_evidence=dataclasses.replace(
                        origin.classification_evidence, **{name: bad}))
                    validation = model.validate_assessment(submitted)
                    self.assertEqual(validation.status, 'REJECTED')
                    self.assertEqual(validation.failure_code, 'PREDICATE_BINDING_MISMATCH')
                    self.assertEqual(validation.field_name,
                                     'origin_assessment.classification_evidence.' + name + '.binding.' + field)
        consulted = origin.classification_evidence.correction_path_is_known
        not_evaluated = sv.NotEvaluatedPredicate(consulted.binding, 'Controlled unavailable consulted predicate.')
        submitted = reflectively_forged(origin, consulted_predicates=(), classification_evidence=dataclasses.replace(
            origin.classification_evidence, correction_path_is_known=not_evaluated))
        validation = model.validate_assessment(submitted)
        self.assertEqual(validation.failure_code, 'PREDICATE_NOT_EVALUATED')
        self.assertEqual(validation.field_name,
                         'origin_assessment.classification_evidence.correction_path_is_known.evaluation')

    def test_pure_validation_all_nine_source_fields_and_owned_prose_boundary(self):
        model, origin, *_ = self.fixture(original=0)
        for field in ('dependency_id', 'aggregate_sha256', *SOURCE_FIELDS):
            with self.subTest(field=field):
                replacement = 'foreign:canonical' if field == 'dependency_id' else 'f' * 64
                submitted = reflectively_forged(origin, source_binding=reflectively_forged(
                    origin.source_binding, **{field: replacement}))
                validation = model.validate_assessment(submitted)
                self.assertEqual(validation.failure_code, 'SOURCE_BINDING_MISMATCH')
                self.assertEqual(validation.field_name, 'origin_assessment.source_binding')
                self.assertIsNone(validation.expected_diagnostic)
        # Owned explanatory prose is retained; it is not an arithmetic oracle.
        notes = ('Independently authored explanatory diagnosis text.',)
        diagnosis = dataclasses.replace(origin.state_validity_diagnostic, notes=notes)
        detection = dataclasses.replace(origin.emitted_diagnostics[0], envelope=dataclasses.replace(
            origin.emitted_diagnostics[0].envelope, notes=notes, summary='Independent valid diagnosis summary.'))
        classification = dataclasses.replace(origin.emitted_diagnostics[1], envelope=dataclasses.replace(
            origin.emitted_diagnostics[1].envelope, notes=('Independent classification explanation.',),
            summary='Independent classification summary.'))
        submitted = dataclasses.replace(origin, state_validity_diagnostic=diagnosis,
                                        emitted_diagnostics=(detection, classification))
        self.assertEqual(model.validate_assessment(submitted).status, 'VERIFIED')
        incoherent = reflectively_forged(submitted, emitted_diagnostics=(origin.emitted_diagnostics[0], classification))
        self.assertEqual(model.validate_assessment(incoherent).failure_code, 'DIAGNOSIS_MISMATCH')

    def test_origin_rejection_precedes_admission_and_all_ports(self):
        model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture()
        submitted = reflectively_forged(origin, state_validity_diagnostic=reflectively_forged(
            origin.state_validity_diagnostic, is_valid=True))
        result = engine.recover(submitted, operation_context=operation(submitted))
        self.assertEqual(result.failure_detail.failure_code, 'ORIGIN_REJECTED')
        self.assertEqual(result.origin_validation.failure_code, 'DIAGNOSIS_MISMATCH')
        self.assertEqual(result.failure_detail.submitted_evidence, result.origin_validation)
        self.assertEqual(result.emitted_diagnostics, ())
        self.assertEqual(result.steps, ())
        self.assertEqual([call for call in diagnostics.calls if call[0] in ('begin', 'begin_denial', 'finish')], [])
        self.assertEqual((resolver.calls, provider.calls, evaluator.calls, post.calls), ([], [], [], []))

    def test_direct_foreign_registry_refuses_before_admission_and_after_correction_keeps_prefix(self):
        source = sv.ProfileSourceBinding('n2:shared:source', 'a' * 64, 'n2:shared:evidence')
        diagnostics = ControlledDiagnostics()
        current = StateModel(profile((0,), source=source), canonical_binding(), diagnostics.assessment_capture())
        foreign = StateModel(profile((0, self.g2), source=source), canonical_binding(), RecordingDiagnosticCapture())
        stale_registry = registry(foreign)
        for known in (False, True):
            with self.subTest(known=known):
                origin = assessment(current, ash(self.g1 if known else 1), known=known, fallback=not known)
                resolver, provider, evaluator, post = NormalizationResolver(current), CorrectionProvider(), Conditions(), PostFacts(current.profile_binding)
                engine = RecoveryEngine(current, stale_registry, diagnostics, resolver, provider, evaluator, post)
                before = len(diagnostics.calls)
                result = engine.recover(origin, operation_context=operation(origin, 'n2:registry:operation:' + str(known)))
                self.assertEqual(result.failure_detail.failure_code, 'REGISTRY_BINDING_REJECTED')
                self.assertEqual(result.registry_validation.failure_code, 'REGISTRY_PROFILE_MISMATCH')
                self.assertEqual(evaluator.calls, [])
                self.assertEqual(post.calls, [])
                if known:
                    self.assertEqual(len(provider.calls), 1)
                    self.assertEqual([step.action for step in result.steps], ['CORRECTION_RESOLVE'])
                    self.assertEqual([decision.action for decision in result.action_decisions], ['CORRECT'])
                    self.assertEqual(len(result.emitted_diagnostics), 2)
                    self.assertEqual(result.action_decisions[0].diagnostic.outcome, 'BLOCKED')
                else:
                    self.assertEqual(result.emitted_diagnostics, ())
                    self.assertEqual(result.steps, ())
                    self.assertEqual([call for call in diagnostics.calls[before:] if call[0] == 'begin'], [])
                    self.assertEqual(provider.calls, [])

    def test_successful_normalization_and_correction_do_not_consult_unused_foreign_registry(self):
        source = sv.ProfileSourceBinding('n2:shared:source', 'a' * 64, 'n2:shared:evidence')
        for known in (False, True):
            diagnostics = ControlledDiagnostics()
            current = StateModel(profile((0,), source=source), canonical_binding(), diagnostics.assessment_capture())
            foreign = StateModel(profile((0, self.g2), source=source), canonical_binding(), RecordingDiagnosticCapture())
            stale = registry(foreign)
            origin = assessment(current, ash(self.g1), known=known)
            provider = CorrectionProvider(known_correction(origin, (self.g1,), 0))
            resolver = NormalizationResolver(current)
            engine = RecoveryEngine(current, stale, diagnostics, resolver, provider, Conditions(), PostFacts(current.profile_binding))
            with mock.patch.object(FallbackRegistry, 'validate_for_model', side_effect=AssertionError('Unused registry consulted')):
                result = engine.recover(origin, operation_context=operation(origin))
            self.assertEqual(result.outcome, 'RECOVERED_VALUE')
            self.assertIsNone(result.registry_validation)
            self.assertIsNone(result.registry_snapshot)

    def test_typed_post_and_predicate_unavailability_are_not_false_try_next(self):
        entries, observations = entries_for((2, 1, 1))
        for mode, code in [('UNAVAILABLE', 'POST_EVIDENCE_UNAVAILABLE'), ('THROW', 'COLLABORATOR_FAILED'),
                           ('BAD_BINDING', 'COLLABORATOR_FAILED')]:
            with self.subTest(post=mode):
                post = PostFacts(profile(), mode=mode)
                model, origin, engine, diagnostics, resolver, provider, evaluator, _ = self.fixture(
                    original=1, fallback=True, entries=entries, conditions=Conditions(observations), post=post)
                result = engine.recover(origin, operation_context=operation(origin))
                self.assertEqual(result.failure_detail.failure_code, code)
                self.assertEqual(len(post.calls), 1)
                self.assertEqual([call for call in evaluator.calls if call[1] == 'ADDITIONAL_VALIDATION'], [])
        for mode in ('UNAVAILABLE', 'THROW', 'BAD_BINDING'):
            with self.subTest(predicate=mode):
                values = dict(observations)
                if mode == 'UNAVAILABLE':
                    values['FALLBACK-STATE-001:app:0'] = 'UNAVAILABLE'
                evaluator = Conditions(values, mode=None if mode == 'UNAVAILABLE' else mode)
                model, origin, engine, diagnostics, resolver, provider, _, post = self.fixture(
                    original=1, fallback=True, entries=entries, conditions=evaluator)
                result = engine.recover(origin, operation_context=operation(origin))
                self.assertEqual(result.failure_detail.failure_code, 'COLLABORATOR_FAILED')
                self.assertEqual(len(evaluator.calls), 1)
                self.assertEqual(post.calls, [])
                if mode == 'UNAVAILABLE':
                    self.assertEqual(result.steps[-1].predicate_observation.status, 'UNAVAILABLE')
                    self.assertEqual(result.failure_detail.submitted_evidence, result.steps[-1].predicate_observation)

    def test_halt_priority_preserves_all_underlying_semantic_rows_without_recovery_ports(self):
        configurations = [((0,), 0, False, False), ((0,), self.g1, False, False),
                          ((0,), self.g1, True, False), ((0,), 1, False, True),
                          ((0,), 1, False, False), ((), self.g1, True, False), ((self.g2,), self.g2, False, False)]
        for states, original, known, fallback in configurations:
            with self.subTest(states=states, original=original, known=known, fallback=fallback):
                model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture(
                    states=states, original=original, known=known, fallback=fallback, halt=True, contained=True)
                result = engine.recover(origin, operation_context=operation(origin))
                self.assertEqual(origin.system_state_class, 'SAFE_HALT')
                self.assertEqual(result.directive.requested_action, 'REMAIN_SAFE_HALT')
                self.assertEqual(result.origin_assessment.state_validity_diagnostic, origin.state_validity_diagnostic)
                self.assertEqual(len(result.emitted_diagnostics), 1)
                self.assertEqual(result.emitted_diagnostics[0].envelope.stage, 'DETECTION')
                self.assertIsNone(result.emitted_diagnostics[0].envelope.parent_diagnostic_reference)
                self.assertEqual((resolver.calls, provider.calls, evaluator.calls, post.calls), ([], [], [], []))
                self.assert_no_value_effects(result)

    def test_hostile_metaclass_and_conversion_hooks_do_not_run_at_exact_input_boundaries(self):
        touched = []
        class HostileMeta(type):
            def __eq__(cls, other):
                touched.append('metaclass equality')
                raise AssertionError('Hostile type equality ran')
            __hash__ = type.__hash__
        class Hostile(metaclass=HostileMeta):
            def __iter__(self):
                touched.append('iteration')
                raise AssertionError('Hostile iteration ran')
            def __str__(self):
                touched.append('string')
                raise AssertionError('Hostile string conversion ran')
            def __int__(self):
                touched.append('integer')
                raise AssertionError('Hostile integer conversion ran')
        model, origin, *_ = self.fixture()
        with self.assertRaises(sv.StateContractError):
            model.inspect_state(Hostile())
        with self.assertRaises(rv.RecoveryContractError):
            model.validate_assessment(Hostile())
        with self.assertRaises(rv.RecoveryContractError):
            model.validate_known_correction(Hostile(), origin=origin)
        self.assertEqual(touched, [])

    def test_reflectively_corrupted_child_types_are_refused_before_hooks_or_ports(self):
        touched = []
        class HostileMeta(type):
            def __eq__(cls, other):
                touched.append('metaclass equality')
                raise AssertionError('Untrusted metaclass equality ran')
            __hash__ = type.__hash__
        class Hostile(metaclass=HostileMeta):
            def __eq__(self, other):
                touched.append('instance equality')
                raise AssertionError('Untrusted child equality ran')
            def __getattr__(self, field):
                touched.append('attribute ' + field)
                raise AssertionError('Untrusted child attribute hook ran')
            def __iter__(self):
                touched.append('iteration')
                raise AssertionError('Untrusted child iteration ran')
            def __str__(self):
                touched.append('conversion')
                raise AssertionError('Untrusted child conversion ran')
        for field in ('source_binding', 'profile_binding', 'parsed_state'):
            for label, child in (('instance', Hostile()), ('class', Hostile)):
                with self.subTest(field=field, child=label):
                    model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture()
                    submitted = reflectively_forged(origin, **{field: child})
                    before = list(diagnostics.calls)
                    validation = model.validate_assessment(submitted)
                    self.assertIs(type(validation), rv.AssessmentValidation)
                    self.assertEqual(validation.status, 'REJECTED')
                    self.assertEqual(touched, [])
                    self.assertEqual(diagnostics.calls, before)
                    result = engine.recover(submitted, operation_context=operation(submitted))
                    self.assertEqual(result.outcome, 'FAILURE')
                    self.assertEqual(result.failure_detail.failure_code, 'ORIGIN_REJECTED')
                    self.assertEqual(result.emitted_diagnostics, ())
                    self.assertEqual(result.steps, ())
                    self.assertEqual(diagnostics.calls, before)
                    self.assertEqual((resolver.calls, provider.calls, evaluator.calls, post.calls), ([], [], [], []))
                    self.assertEqual(touched, [])

    def test_nested_binding_and_semantic_equality_cannot_forge_pure_validation(self):
        touched = []
        class ForgedEquality:
            def __eq__(self, other):
                touched.append('nested equality')
                return True
            def __getattr__(self, field):
                touched.append('nested attribute ' + field)
                raise AssertionError('Untrusted nested attribute ran')
        for field in ('canonical_hash', 'profile_child', 'profile_source', 'profile_id',
                      'validity_boolean', 'orbit_boolean'):
            with self.subTest(field=field):
                model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture()
                hostile = ForgedEquality()
                if field == 'canonical_hash':
                    submitted = reflectively_forged(origin, source_binding=reflectively_forged(
                        origin.source_binding, aggregate_sha256=hostile))
                elif field == 'profile_child':
                    submitted = reflectively_forged(origin, profile_binding=reflectively_forged(
                        origin.profile_binding, profile=hostile))
                elif field in ('profile_source', 'profile_id'):
                    changes = {'source_binding' if field == 'profile_source' else 'profile_id': hostile}
                    submitted = reflectively_forged(origin, profile_binding=reflectively_forged(
                        origin.profile_binding, profile=reflectively_forged(origin.profile_binding.profile, **changes)))
                else:
                    diagnostic = origin.state_validity_diagnostic
                    changes = ({'is_valid':hostile} if field == 'validity_boolean' else
                               {'orbit_info':reflectively_forged(diagnostic.orbit_info, contains_known_valid_state=hostile)})
                    submitted = reflectively_forged(origin, state_validity_diagnostic=reflectively_forged(diagnostic, **changes))
                before = list(diagnostics.calls)
                validation = model.validate_assessment(submitted)
                self.assertEqual(validation.status, 'REJECTED')
                self.assertEqual(touched, [])
                result = engine.recover(submitted, operation_context=operation(submitted))
                self.assertEqual(result.outcome, 'FAILURE')
                self.assertEqual(result.failure_detail.failure_code, 'ORIGIN_REJECTED')
                self.assertEqual(result.emitted_diagnostics, ())
                self.assertEqual(result.steps, ())
                self.assertEqual(diagnostics.calls, before)
                self.assertEqual((resolver.calls, provider.calls, evaluator.calls, post.calls), ([], [], [], []))
                self.assertEqual(touched, [])

    def test_correction_declaration_nested_guards_precede_equality_and_xor(self):
        touched = []
        class ForgedEquality:
            def __eq__(self, other):
                touched.append('correction equality')
                return True
        model, origin, *_ = self.fixture(known=True)
        declared = known_correction(origin, (self.g1,), 0)
        for field in ('canonical_hash', 'profile_id', 'origin_reference', 'chain_bit', 'target_bit'):
            with self.subTest(field=field):
                hostile = ForgedEquality()
                if field == 'canonical_hash':
                    submitted = reflectively_forged(declared, canonical_binding=reflectively_forged(
                        declared.canonical_binding, aggregate_sha256=hostile))
                elif field in ('profile_id', 'origin_reference'):
                    submitted = reflectively_forged(declared, **{
                        'profile_id' if field == 'profile_id' else 'original_assessment_reference': hostile})
                elif field == 'chain_bit':
                    submitted = reflectively_forged(declared, chain=(reflectively_forged(
                        declared.chain[0], bits=(hostile,) + declared.chain[0].bits[1:]),))
                else:
                    submitted = reflectively_forged(declared, expected_target=reflectively_forged(
                        declared.expected_target, bits=(hostile,) + declared.expected_target.bits[1:]))
                if field in ('canonical_hash', 'chain_bit'):
                    validation = model.validate_known_correction(submitted, origin=origin)
                    self.assertEqual(validation.status, 'REJECTED')
                    self.assertEqual(validation.failure_code, 'SOURCE_BINDING_MISMATCH' if field == 'canonical_hash' else 'CHAIN_MEMBER_INVALID')
                else:
                    with self.assertRaises(rv.RecoveryContractError):
                        model.validate_known_correction(submitted, origin=origin)
                self.assertEqual(touched, [])

    def test_actual32_candidate_transaction_retains_every_predicate_and_compact_summary(self):
        entries, observations = [], {}
        for index in range(32, 0, -1):
            policy = f'FALLBACK-STATE-{index:03d}'
            applicability = tuple(rv.ConditionReference(policy + ':app:' + str(n), evidence_source()) for n in range(8))
            validation = tuple(rv.ConditionReference(policy + ':validation:' + str(n), evidence_source()) for n in range(8))
            for condition in applicability + validation:
                observations[condition.condition_id] = 'TRUE'
            if index != 32:
                observations[validation[-1].condition_id] = 'FALSE'
            entries.append(rv.FallbackPolicyEntry(policy, applicability, ash(0), index, validation,
                                                  'TRY_NEXT', ('Maximum actual bounded candidate test.',)))
        model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture(
            known=True, entries=entries, conditions=Conditions(observations))
        result = engine.recover(origin, operation_context=operation(origin))
        self.assertEqual(result.outcome, 'RECOVERED_FALLBACK_VALUE')
        self.assertEqual(len(result.policy_attempts), 32)
        self.assertEqual(len(result.post_assessments), 32)
        self.assertEqual(len(evaluator.calls), 512)
        self.assertEqual(len(result.action_decisions), 34)  # failed correction +32 candidates +summary
        self.assertEqual([attempt.policy_id for attempt in result.policy_attempts],
                         [f'FALLBACK-STATE-{index:03d}' for index in range(1, 33)])
        summary = result.action_decisions[-1]
        self.assertEqual(summary.action, 'FALLBACK_SUMMARY')
        self.assertEqual(len(summary.diagnostic.steps), 32)
        detailed = [step for step in result.steps if step.action in ('CANDIDATE_APPLICABILITY', 'CANDIDATE_VALIDATION')]
        self.assertEqual(len(detailed), 512)
        self.assertTrue(all(step.step_index in summary.step_indices for step in detailed))
        self.assertLessEqual(len(result.steps), 768)
        self.assertEqual(len(diagnostics.finish_inputs), 1)
        self.assert_chain(result)

    def test_known_proof_exact_origin_and_binding_comparisons_retain_submitted_declaration(self):
        model, origin, *_ = self.fixture(known=True)
        submitted = known_correction(origin, (self.g1,), 0)
        variants = [
            ('SOURCE_BINDING_MISMATCH', reflectively_forged(submitted, canonical_binding=reflectively_forged(
                submitted.canonical_binding, recovery_source_sha256='f' * 64))),
            ('PROFILE_BINDING_MISMATCH', dataclasses.replace(submitted, profile_id='foreign:profile')),
            ('PROFILE_BINDING_MISMATCH', dataclasses.replace(submitted, profile_source_sha256='f' * 64)),
            ('ORIGIN_MISMATCH', dataclasses.replace(submitted, original_assessment_reference='foreign:assessment')),
            ('ORIGIN_MISMATCH', dataclasses.replace(submitted, classification_evidence_reference='foreign:known:fact')),
        ]
        for code, candidate in variants:
            with self.subTest(code=code):
                validation = model.validate_known_correction(candidate, origin=origin)
                self.assertEqual(validation.status, 'REJECTED')
                self.assertEqual(validation.failure_code, code)
                self.assertEqual(validation.submitted_correction, candidate)
                self.assertEqual(validation.origin_validation.status, 'VERIFIED')
                self.assertIsNone(validation.computed_target)
                self.assertIsNone(validation.target_diagnostic)
        # Provider hashes are declarations; current full source and arithmetic are verified independently.
        different_declaration = dataclasses.replace(submitted, source_binding=evidence_source('declared:other:provider'))
        self.assertEqual(model.validate_known_correction(different_declaration, origin=origin).status, 'VERIFIED')
        rejected_origin = reflectively_forged(origin, state_validity_diagnostic=reflectively_forged(
            origin.state_validity_diagnostic, normalization_status='NOT_NORMALIZABLE'))
        validation = model.validate_known_correction(submitted, origin=rejected_origin)
        self.assertEqual(validation.failure_code, 'ORIGIN_MISMATCH')
        self.assertEqual(validation.origin_validation.status, 'REJECTED')
        self.assertEqual(validation.origin_validation.submitted_assessment, rejected_origin)
        self.assertIsNone(validation.computed_target)
        self.assertIsNone(validation.target_diagnostic)

    def test_correction_provider_failures_and_unavailable_fact_binding_are_distinct(self):
        for mode in ('THROW', 'NONE', 'FOREIGN_FACT'):
            with self.subTest(mode=mode):
                model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture(known=True)
                if mode == 'THROW':
                    provider.throw = True
                elif mode == 'FOREIGN_FACT':
                    provider.result = dataclasses.replace(unavailable_correction(origin),
                                                         classification_evidence_reference='foreign:known:fact')
                else:
                    provider.resolve = mock.Mock(return_value=None)
                result = engine.recover(origin, operation_context=operation(origin))
                self.assertEqual(result.failure_detail.failure_code, 'COLLABORATOR_FAILED')
                self.assertIsNone(result.route_authorization)
                self.assertIsNone(result.registry_validation)
                self.assertEqual(evaluator.calls, [])
                self.assertEqual(post.calls, [])
                self.assert_no_value_effects(result)

    def test_failed_handoff_capture_retains_mandatory_directive_without_claiming_entry(self):
        for mode in ('REJECTED', 'THROW_AFTER'):
            diagnostics = ControlledDiagnostics(
                fail=lambda record: record.record_kind == 'OPERATION_DECISION' and record.payload.action == 'HANDOFF',
                mode=mode)
            model, origin, engine, _, resolver, provider, evaluator, post = self.fixture(
                norm='UNAVAILABLE', diagnostics=diagnostics)
            result = engine.recover(origin, operation_context=operation(origin))
            self.assertEqual(result.outcome, 'FAILURE')
            self.assertEqual(result.failure_detail.failure_code,
                             'STEP_CAPTURE_REJECTED' if mode == 'REJECTED' else 'STEP_CAPTURE_UNCONFIRMED')
            self.assertEqual(result.failure_detail.pending_directive, result.directive)
            self.assertEqual(result.directive.requested_action, 'ENTER_CONTAINMENT')
            self.assertEqual(result.directive.actual_mode_status, 'NOT_ENTERED_BY_N2')
            self.assertEqual(result.failure_detail.attempted_diagnostic.payload.directive, result.directive)
            self.assertEqual(result.action_decisions[-1].action, 'HANDOFF')
            self.assertEqual(result.emitted_diagnostics[-1].payload.action, 'NORMALIZE')
            self.assert_no_value_effects(result)

    def test_all15_nonzero_codewords_reach_actual_normalization_and_known_correction(self):
        for original, known in itertools.product((word for word in self.words if word), (False, True)):
            with self.subTest(original=original, known=known):
                model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture(
                    original=original, known=known)
                if known:
                    provider.result = known_correction(origin, (original,), 0)
                result = engine.recover(origin, operation_context=operation(origin))
                self.assertEqual(origin.system_state_class, 'CORRECTABLE' if known else 'UNSTABLE')
                self.assertEqual(result.outcome, 'RECOVERED_VALUE')
                self.assertEqual(number(result.candidate_state), original ^ original)
                steps = [step for step in result.steps if step.action in ('NORMALIZE_XOR', 'CORRECTION_XOR')]
                self.assertEqual(len(steps), 1)
                self.assertEqual((number(steps[0].before_state), number(steps[0].codeword), number(steps[0].after_state)),
                                 (original, original, 0))
                self.assertEqual(len(post.calls), 1)
                self.assertEqual(result.post_assessments[0].assessment.system_state_class, 'STABLE')
                self.assertEqual(result.post_assessments[0].assessment.parsed_state, ash(0))
                self.assert_chain(result)

    def test_unavailable_profile_and_rejected_input_preserve_actual_unclassified_origin(self):
        unavailable = sv.UnavailableProfileBinding(sv.UnavailableValidityProfileEvidence(
            'n2:unavailable', sv.ProfileSourceBinding('n2:source', 'a' * 64, 'n2:evidence'),
            'PROFILE_DATA_UNAVAILABLE', 'Explicitly unavailable profile.'))
        for binding, candidate in [(unavailable, ash(self.g1)), (profile(), [0] * 8), (profile(), object())]:
            with self.subTest(availability=binding.availability, candidate_type=type(candidate).__name__):
                diagnostics = ControlledDiagnostics()
                model = StateModel(binding, canonical_binding(), diagnostics.assessment_capture())
                origin = assessment(model, candidate, known=None, fallback=None)
                self.assertIs(type(origin), sv.StateAssessment)
                self.assertEqual(origin.state_validity_diagnostic.admissibility_status, 'UNCLASSIFIED')
                self.assertEqual(origin.system_state_class, 'DEGRADED')
                self.assertEqual(origin.consulted_predicates, ())
                resolver, provider, evaluator, post = NormalizationResolver(model), CorrectionProvider(), Conditions(), PostFacts(binding)
                engine = RecoveryEngine(model, registry(model), diagnostics, resolver, provider, evaluator, post)
                result = engine.recover(origin, operation_context=operation(origin))
                self.assertEqual(result.outcome, 'HANDOFF_REQUIRED')
                self.assertEqual(result.directive.requested_action, 'ENTER_CONTAINMENT')
                self.assertEqual(result.origin_assessment.input_evidence, origin.input_evidence)
                self.assertEqual(result.origin_assessment.parsed_state, origin.parsed_state)
                self.assertEqual(result.route_authorization.route, 'DIRECT_DEGRADED')
                self.assertEqual((resolver.calls, provider.calls, evaluator.calls, post.calls), ([], [], [], []))
                self.assert_no_value_effects(result)

    def test_controlled_arithmetic_defect_is_infrastructure_refusal_before_post_or_fallback(self):
        # Trusted proof/XOR owners cannot naturally produce a wrong VALID target.
        # This deliberate helper defect is not ordinary after-normalization-failure coverage.
        for known in (False, True):
            model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture(
                states=(0, self.g2), known=known)
            if known:
                provider.result = known_correction(origin, (self.g1,), 0)
            with mock.patch('core.ash_pattern_engine.recovery._apply_codeword', return_value=ash(self.g2)) as defective:
                result = engine.recover(origin, operation_context=operation(origin))
            self.assertEqual(defective.call_count, 1)
            self.assertEqual(result.outcome, 'FAILURE')
            self.assertEqual(result.failure_detail.failure_code, 'INTERNAL_INVARIANT_FAILURE')
            self.assertEqual(result.origin_assessment, origin)
            self.assertEqual(number(result.candidate_state), self.g2)
            self.assertEqual(post.calls, [])
            self.assertEqual(evaluator.calls, [])
            self.assertIsNone(result.route_authorization)
            self.assertIsNone(result.registry_validation)
            self.assertEqual([step for step in result.steps if step.action.endswith('_XOR')], [])
            self.assertEqual(len(result.emitted_diagnostics), 1)
            self.assertEqual(len(diagnostics.finish_inputs), 1)

    def test_shared_eight_rule_envelope_keeps_assessment_six_and_normalization_seven_guards(self):
        from core.ash_pattern_engine.normalization import RecordingNormalizationCapture
        model, origin, *_ = self.fixture()
        diagnosis = model.diagnosis_from_assessment(origin)
        seven = (*DIAGNOSIS_RULES, 'ASH-CODEWORD-STRUCTURE-001')
        with self.assertRaises(sv.StateContractError) as error:
            dataclasses.replace(diagnosis.state_validity_diagnostic, rule_ids=seven)
        self.assertEqual((error.exception.code, error.exception.field_name),
                         ('DIAGNOSTIC_ROW_INVALID', 'rule_ids'))
        row = reflectively_forged(diagnosis.state_validity_diagnostic, rule_ids=seven)
        with self.assertRaises(sv.StateContractError) as error:
            dataclasses.replace(diagnosis, state_validity_diagnostic=row)
        self.assertEqual((error.exception.code, error.exception.field_name),
                         ('DIAGNOSTIC_ROW_INVALID', 'state_validity_diagnostic.rule_ids'))
        normalizer = StateModel(model.profile_binding, model.canonical_binding, RecordingDiagnosticCapture(),
                                normalization_capture=RecordingNormalizationCapture())
        plan = normalizer.plan_normalization(diagnosis, plan_reference='n2:legacy:plan',
                                              evidence_reference='n2:legacy:proof', policy_binding=normalization_policy())
        result = normalizer.apply_normalization(plan, normalization_context=nv.NormalizationContext(
            'n2:legacy:operation', 'n2:legacy:computation', 'n2:legacy:post'))
        self.assertEqual(result.outcome, 'NORMALIZED')
        for rule in ('ASH-FALLBACK-SELECTION-001', 'ASH-CONTAINMENT-TRIGGER-001', 'ASH-HALT-TRIGGER-001'):
            with self.subTest(rule=rule):
                envelope = dataclasses.replace(result.emitted_diagnostics[0].emission.envelope, rule_ids=(rule,))
                self.assertEqual(envelope.rule_ids, (rule,))  # generic owner recognizes canonical rule
                emission = dataclasses.replace(result.emitted_diagnostics[0].emission, envelope=envelope)
                with self.assertRaises(nv.NormalizationContractError) as error:
                    dataclasses.replace(result.emitted_diagnostics[0], emission=emission)
                self.assertEqual((error.exception.code, error.exception.field_name),
                                 ('NORMALIZATION_PLAN_INVALID', 'emission.envelope.rule_ids'))
                shared = dataclasses.replace(diagnosis.emitted_diagnostics[0].envelope, rule_ids=(rule,))
                with self.assertRaises(sv.StateContractError) as error:
                    dataclasses.replace(diagnosis, emitted_diagnostics=(sv.DiagnosticEmission(
                        diagnosis.emitted_diagnostics[0].diagnostic_reference, shared),))
                self.assertEqual((error.exception.code, error.exception.field_name),
                                 ('DIAGNOSTIC_ENVELOPE_INVALID', 'emitted_diagnostics'))

    def test_every_lifecycle_rule_is_refused_by_unchanged_eight_rule_recovery_owners(self):
        _, origin, engine, *_ = self.fixture(original=0)
        result = engine.recover(origin, operation_context=operation(origin))
        record = result.emitted_diagnostics[0]
        lifecycle_rules = sv.RULE_IDS - rv.N2_RULE_IDS
        self.assertEqual(len(lifecycle_rules), 9)
        self.assertEqual(len(rv.N2_RULE_IDS), 8)
        for rule in sorted(lifecycle_rules):
            with self.subTest(rule=rule):
                envelope = dataclasses.replace(record.envelope, rule_ids=(rule,))
                self.assertEqual(envelope.rule_ids, (rule,))
                with self.assertRaises(rv.RecoveryContractError) as error:
                    dataclasses.replace(record, envelope=envelope)
                self.assertEqual(error.exception.field_name, 'emitted_diagnostics')
                reflected = reflectively_forged(record, envelope=envelope)
                with self.assertRaises(rv.RecoveryContractError):
                    dataclasses.replace(result, emitted_diagnostics=(reflected,))
                detail = rv.RecoveryFailureDetail('STEP_CAPTURE_REJECTED', 'capture.append', None,
                    record, 'REJECTED', None, 'Controlled attempted-record refusal.', None, None)
                with self.assertRaises(rv.RecoveryContractError):
                    dataclasses.replace(detail, attempted_diagnostic=reflected)
                reflected_detail = reflectively_forged(detail, attempted_diagnostic=reflected)
                with self.assertRaises(rv.RecoveryContractError):
                    rv.RecoveryFailure(**{field.name: getattr(result, field.name) for field in dataclasses.fields(result)}
                                       | {'failure_detail': reflected_detail})

    def test_registry_reported_stability_is_rederived_and_never_a_collector_ack(self):
        model, origin, engine, diagnostics, *_ = self.fixture(original=1, fallback=True)
        entry = entries_for((1, 1, 1))[0][-1]
        binding = rv.RegistrySourceBinding('n2:registry', evidence_source('n2:registry:source'),
                                           model.profile_binding.profile_id, model.profile_binding.source_binding.source_sha256,
                                           DEPENDENCY, AGGREGATE)
        source_assessment = assessment(model, ash(0), reference='n2:contained:certification',
                                       known=None, fallback=None, contained=True)
        certification = rv.CandidateCertification(entry.policy_id, rv.ContextObservation(
            source_assessment.system_context, 'n2:certificate:owner', 'n2:certificate:context', evidence_source()),
            source_assessment)
        snapshot = rv.AvailableFallbackRegistry(binding, (entry,), (certification,))
        with self.assertRaises(rv.RecoveryContractError) as error:
            FallbackRegistry(snapshot, state_model=model)
        self.assertEqual(error.exception.validation.failure_code, 'CERTIFICATION_NOT_STABLE')
        self.assertEqual(error.exception.validation.candidate_validations[0].assessment_validation.status, 'VERIFIED')
        self.assertEqual(error.exception.validation.candidate_validations[0].submitted_certification, certification)
        self.assertEqual(diagnostics.records, [])

    def test_signed_rank_then_id_order_and_first_false_short_circuit_are_actual(self):
        entries, observations = entries_for((1, 1, 1))
        # Lowest signed rank precedes both tied IDs; declaration order remains independent.
        entries = tuple(dataclasses.replace(entry, ordering_rank=-(1 << 63) if entry.policy_id.endswith('003') else 0)
                        for entry in entries)
        observations['FALLBACK-STATE-003:app:0'] = 'FALSE'
        model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture(
            original=1, fallback=True, entries=entries, conditions=Conditions(observations))
        self.assertEqual([entry.policy_id for entry in engine._registry.ordered_entries()],
                         ['FALLBACK-STATE-003', 'FALLBACK-STATE-001', 'FALLBACK-STATE-002'])
        result = engine.recover(origin, operation_context=operation(origin))
        self.assertEqual(result.outcome, 'RECOVERED_FALLBACK_VALUE')
        self.assertEqual(evaluator.calls[0], ('FALLBACK-STATE-003', 'APPLICABILITY', 'FALLBACK-STATE-003:app:0'))
        self.assertNotIn(('FALLBACK-STATE-003', 'APPLICABILITY', 'FALLBACK-STATE-003:app:1'), evaluator.calls)
        ineligible = next(attempt for attempt in result.policy_attempts if attempt.policy_id.endswith('003'))
        self.assertEqual(ineligible.result, 'INELIGIBLE')
        self.assertEqual([condition.condition_id for condition in ineligible.unconsulted_applicability],
                         ['FALLBACK-STATE-003:app:1'])
        self.assertEqual(result.action_decisions[-1].diagnostic.fallback_policy_id, 'FALLBACK-STATE-001')

    def test_pure_inspection2048_rows_use_independent_complete_orbit_membership(self):
        class NoCapture:
            def begin(self, *_args, **_kwargs):
                raise AssertionError('Pure inspect_state attempted capture')
        profile_states = [(0,), (), (0, self.g1, self.g2),
                          (0, 1, 2, 4, 8, 16, 32, 64, 128)]
        for recognized in profile_states:
            model = StateModel(profile(recognized), canonical_binding(), NoCapture())
            for state in range(512):
                with self.subTest(recognized=recognized, state=state):
                    members = sorted(state ^ word for word in self.words)
                    targets = [member for member in members if member in recognized]
                    valid = state in recognized
                    status = 'VALID' if valid else 'TRANSFORMATION_COMPATIBLE' if targets else 'TRANSFORMATION_INCOMPATIBLE'
                    diagnostic = model.inspect_state(ash(state))
                    self.assertEqual(diagnostic.input_state, ash(state))
                    self.assertEqual(diagnostic.admissibility_status, status)
                    self.assertEqual(diagnostic.transformation_compatibility, 'COMPATIBLE' if targets else 'INCOMPATIBLE')
                    self.assertEqual(diagnostic.normalization_status,
                                     'ALREADY_VALID' if valid else 'NORMALIZABLE' if targets else 'NOT_NORMALIZABLE')
                    self.assertEqual(diagnostic.recoverability_relevance,
                                     'NO_RECOVERY_NEEDED' if valid else 'RECOVERY_APPLICABLE' if targets else 'NOT_RECOVERABLE')
                    self.assertEqual(diagnostic.is_valid, valid)
                    self.assertEqual(diagnostic.orbit_info, sv.OrbitInfo(format(members[0], '09b'), 16, bool(targets)))
                    self.assertEqual(diagnostic.rule_ids, DIAGNOSIS_RULES)

    def test_mutated_origin_empty_partial_and_wrong_chain_never_crash_or_seed_capture(self):
        model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture()
        first, second = origin.emitted_diagnostics
        wrong_parent = sv.DiagnosticEmission(second.diagnostic_reference, dataclasses.replace(
            second.envelope, parent_diagnostic_reference='foreign:root'))
        variants = [(), (first,), (second, first), (first, wrong_parent)]
        for emissions in variants:
            with self.subTest(emissions=len(emissions), references=tuple(e.diagnostic_reference for e in emissions)):
                submitted = reflectively_forged(origin, emitted_diagnostics=emissions)
                validation = model.validate_assessment(submitted)
                self.assertEqual(validation.status, 'REJECTED')
                before = len(diagnostics.calls)
                result = engine.recover(submitted, operation_context=operation(submitted))
                self.assertEqual(result.outcome, 'FAILURE')
                self.assertEqual(result.failure_detail.failure_code, 'ORIGIN_REJECTED')
                self.assertEqual(result.origin_validation, validation)
                self.assertEqual(result.emitted_diagnostics, ())
                self.assertEqual(result.steps, ())
                self.assertEqual([call for call in diagnostics.calls[before:] if call[0] in ('begin', 'begin_denial', 'finish')], [])
                self.assertEqual((resolver.calls, provider.calls, evaluator.calls, post.calls), ([], [], [], []))

    def test_completed_semantic_child_failure_is_distinct_from_unconfirmed_capture(self):
        model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture()
        def boundary_probe(operation_owner):
            # Explicit post-boundary injection: trusted READY/XOR paths cannot naturally
            # submit this incompatible value. The actual StateModel result is never mocked.
            operation_owner.candidate = ash(1)
            return operation_owner._post(ash(1), operation_owner._action_reference())
        with mock.patch('core.ash_pattern_engine.recovery._RecoveryOperation._normalize', boundary_probe):
            result = engine.recover(origin, operation_context=operation(origin))
        self.assertEqual(result.outcome, 'FAILURE')
        self.assertEqual(result.failure_detail.failure_code, 'POST_ASSESSMENT_FAILED')
        self.assertIsNone(result.failure_detail.capture_status)
        self.assertEqual(len(result.post_assessments), 1)
        linked = result.post_assessments[0]
        self.assertEqual(linked.capture_status, 'COMPLETE')
        self.assertIs(type(linked.assessment), sv.ClassificationEvidenceFailure)
        self.assertEqual(linked.assessment.state_validity_diagnostic.admissibility_status, 'TRANSFORMATION_INCOMPATIBLE')
        self.assertEqual(linked.assessment.failure_code, 'PREDICATE_NOT_EVALUATED')
        self.assertEqual(linked.assessment.failed_predicate, 'fallback_is_available')
        self.assertEqual(len(linked.assessment.emitted_diagnostics), 1)
        self.assertEqual(linked.assessment.classification_evidence,
                         result.failure_detail.submitted_evidence.classification_evidence)
        self.assertEqual(len([call for call in diagnostics.calls if call[0] == 'complete_assessment']), 1)
        self.assertEqual(len(diagnostics.children[0][1]), 1)
        self.assertEqual((resolver.calls, provider.calls, evaluator.calls), ([], [], []))
        self.assertEqual(len(post.calls), 1)
        self.assertEqual(result.steps, ())
        self.assertIsNone(result.route_authorization)

    def test_all32_dependency_files_and_emitted_seven_source_pins_match_actual_bytes(self):
        manifest = json.loads(legacy_text('data/governance/ash_dependency_identity.json'))
        rows = [(entry['relative_path'], legacy_source_hash(entry['relative_path']))
                for entry in manifest['files']]
        self.assertEqual(len(rows), 32)
        self.assertEqual(len(set(path for path, _ in rows)), 32)
        self.assertEqual(dict(rows), {entry['relative_path']: entry['sha256'] for entry in manifest['files']})
        aggregate = hashlib.sha256(''.join(path + '\0' + digest + '\n'
                                         for path, digest in sorted(rows)).encode('utf-8')).hexdigest()
        self.assertEqual(aggregate, AGGREGATE)
        paths = ('interfaces/contracts/recovery-engine-contract.md',
                 'interfaces/contracts/diagnostics-module-contract.md',
                 'registries/fallback-policy-registry.md', 'algorithms/recovery-fallback-semantics.pseudo.md',
                 'algorithms/containment-safe-failure-semantics.pseudo.md',
                 'interfaces/diagnostic-schema.md', 'interfaces/rule-id-taxonomy.md')
        expected = tuple((path, legacy_source_hash(path)) for path in paths)
        model, origin, engine, *_ = self.fixture(original=0)
        result = engine.recover(origin, operation_context=operation(origin))
        self.assertEqual(tuple((pin.path, pin.sha256) for pin in result.source_binding.contract_pins), expected)
        self.assertEqual(result.source_binding.canonical_binding, canonical_binding())
        self.assertEqual(normalized_hash(ROOT / 'docs/architecture/m3_normalization_policy.md'), N1_POLICY_PIN)

    def test_current32_source_bytes_and_engine_pins_cover_actual_coherent_routes(self):
        manifest = json.loads((ROOT / 'data/governance/ash_dependency_identity.json').read_text(encoding='utf-8'))
        rows = [(entry['relative_path'], normalized_hash(CANONICAL / entry['relative_path']))
                for entry in manifest['files']]
        self.assertEqual(len(rows), 32)
        self.assertEqual(len(set(path for path, _ in rows)), 32)
        self.assertEqual(dict(rows), {entry['relative_path']: entry['sha256'] for entry in manifest['files']})
        aggregate = hashlib.sha256(''.join(path + '\0' + digest + '\n'
                                         for path, digest in sorted(rows)).encode('utf-8')).hexdigest()
        self.assertEqual(aggregate, CURRENT_AGGREGATE)
        expected = tuple((path, normalized_hash(CANONICAL / path)) for path, _ in rv.RECOVERY_CONTRACT_PIN_FIELDS)
        cases = [('STABLE', 0, False, False, False, False, 'NO_ACTION'),
                 ('UNSTABLE', self.g1, False, False, False, False, 'RECOVERED_VALUE'),
                 ('CORRECTABLE', self.g1, True, False, False, False, 'HANDOFF_REQUIRED'),
                 ('DEGRADED', 1, False, True, False, False, 'HANDOFF_REQUIRED'),
                 ('CONTAINED', 0, False, False, False, True, 'HANDOFF_REQUIRED'),
                 ('FAILED', 1, False, False, False, False, 'HANDOFF_REQUIRED'),
                 ('SAFE_HALT', 0, False, False, True, False, 'HANDOFF_REQUIRED')]
        for expected_class, original, known, fallback, halt, contained, expected_outcome in cases:
            with self.subTest(state_class=expected_class):
                model, origin, engine, *_ = self.fixture(original=original, known=known, fallback=fallback,
                    halt=halt, contained=contained, canonical=canonical_binding(current=True))
                result = engine.recover(origin, operation_context=operation(origin))
                self.assertEqual(origin.system_state_class, expected_class)
                self.assertEqual(result.outcome, expected_outcome)
                self.assertEqual(result.source_binding.canonical_binding, model.canonical_binding)
                self.assertEqual(tuple((pin.path, pin.sha256) for pin in result.source_binding.contract_pins), expected)
                self.assertEqual(result.origin_validation.status, 'VERIFIED')
                self.assertEqual(result.completion_observation.status, 'COMPLETE')
                self.assertFalse(result.session_effects_performed)
                for post in result.post_assessments:
                    self.assertEqual(post.assessment.source_binding, model.canonical_binding)

    def test_current_known_correction_and_fallback_success_keep_exact_source_proofs(self):
        entries, observations = entries_for()
        for known in (True, False):
            model, origin, engine, _, _, provider, _, _ = self.fixture(original=self.g1 if known else 1,
                known=known, fallback=not known, canonical=canonical_binding(current=True),
                entries=() if known else entries, conditions=Conditions(observations))
            if known:
                provider.result = known_correction(origin, (self.g1,), 0)
            result = engine.recover(origin, operation_context=operation(origin))
            with self.subTest(known=known):
                self.assertEqual(result.outcome, 'RECOVERED_VALUE' if known else 'RECOVERED_FALLBACK_VALUE')
                self.assertEqual(result.candidate_state, ash(0))
                self.assertEqual(result.source_binding.canonical_binding, model.canonical_binding)
                self.assertEqual(result.post_assessments[0].assessment.source_binding, model.canonical_binding)
                if known:
                    self.assertEqual(result.correction_observation.validation.status, 'VERIFIED')
                    self.assertEqual(result.correction_observation.submitted.canonical_binding, model.canonical_binding)
                else:
                    self.assertEqual(result.registry_validation.status, 'VERIFIED')
                    self.assertEqual(result.registry_snapshot.source_binding.ash_aggregate_sha256, CURRENT_AGGREGATE)

    def test_current_and_legacy_origins_and_registries_cannot_cross_model_authority(self):
        for current in (False, True):
            model, origin, engine, diagnostics, resolver, provider, evaluator, post = self.fixture(
                original=1, fallback=True, canonical=canonical_binding(current=current))
            foreign_model = StateModel(model.profile_binding, canonical_binding(current=not current), RecordingDiagnosticCapture())
            foreign_origin = assessment(foreign_model, ash(1), fallback=True)
            before = len(diagnostics.calls)
            result = engine.recover(foreign_origin, operation_context=operation(foreign_origin))
            with self.subTest(current=current, role='origin'):
                self.assertEqual(result.failure_detail.failure_code, 'ORIGIN_REJECTED')
                self.assertEqual(result.origin_validation.failure_code, 'SOURCE_BINDING_MISMATCH')
                self.assertIs(result.origin_validation.submitted_assessment, foreign_origin)
                self.assertEqual(result.origin_validation.current_source_binding, model.canonical_binding)
                self.assertEqual(result.emitted_diagnostics, ())
                self.assertEqual(result.steps, ())
                self.assertEqual(diagnostics.calls[before:], [])
                self.assertEqual((resolver.calls, provider.calls, evaluator.calls, post.calls), ([], [], [], []))
            foreign_registry = registry(foreign_model)
            foreign_engine = RecoveryEngine(model, foreign_registry, diagnostics, resolver, provider, evaluator, post)
            result = foreign_engine.recover(origin, operation_context=operation(origin))
            with self.subTest(current=current, role='registry'):
                self.assertEqual(result.failure_detail.failure_code, 'REGISTRY_BINDING_REJECTED')
                self.assertEqual(result.registry_validation.failure_code, 'REGISTRY_SOURCE_MISMATCH')
                self.assertIs(result.registry_validation.submitted_snapshot, foreign_registry.snapshot)
                self.assertEqual(result.registry_validation.current_source_binding, model.canonical_binding)
                self.assertEqual(result.emitted_diagnostics, ())
                self.assertEqual(result.steps, ())
                self.assertEqual(diagnostics.calls[before:], [])
                self.assertEqual((resolver.calls, provider.calls, evaluator.calls, post.calls), ([], [], [], []))

    def test_child_completion_failures_preserve_actual_complete_assessment_and_stop_retry(self):
        entries, observations = entries_for((2, 1, 1))
        for mode in ('INCOMPLETE', 'WRONG_REFERENCE', 'NONE', 'THROW'):
            with self.subTest(mode=mode):
                diagnostics = ControlledDiagnostics(post_completion=mode)
                model, origin, engine, _, resolver, provider, evaluator, post = self.fixture(
                    original=1, fallback=True, entries=entries, conditions=Conditions(observations),
                    diagnostics=diagnostics)
                result = engine.recover(origin, operation_context=operation(origin))
                self.assertEqual(result.outcome, 'FAILURE')
                self.assertEqual(result.failure_detail.failure_code,
                                 'POST_CAPTURE_REJECTED' if mode == 'INCOMPLETE' else 'POST_CAPTURE_UNCONFIRMED')
                linked = result.post_assessments[0]
                self.assertIs(type(linked.assessment), sv.StateAssessment)
                self.assertEqual(linked.capture_status, 'REJECTED' if mode == 'INCOMPLETE' else 'NOT_CONFIRMED')
                self.assertEqual(linked.assessment.system_state_class, 'STABLE')
                self.assertEqual(linked.assessment.state_validity_diagnostic.admissibility_status, 'VALID')
                self.assertEqual(len(linked.assessment.emitted_diagnostics), 2)
                self.assertEqual(model.validate_assessment(linked.assessment).status, 'VERIFIED')
                self.assertEqual(diagnostics.children[0][1], list(linked.assessment.emitted_diagnostics))
                self.assertEqual(len(post.calls), 1)
                self.assertEqual(len(result.post_assessments), 1)
                self.assertEqual([call for call in evaluator.calls if call[1] == 'ADDITIONAL_VALIDATION'], [])
                self.assertFalse(any(action.diagnostic.outcome == 'RECOVERED_VIA_FALLBACK'
                                     for action in result.action_decisions))
                self.assertEqual(result.completion_observation.status, 'COMPLETE')  # outer failure completed once
                self.assertEqual(len(diagnostics.finish_inputs), 1)

    @unittest.skipUnless(os.name == "nt", "Actual adopted protected storage is Windows-specific")
    def test_genuine_windows_collector_integrates_n1_recovery_routes_and_paired_redacted_export(self):
        from scripts.reference_diagnostics_host import assemble_reference_diagnostics
        sentinel = 'N2_REFERENCE_SECRET_SENTINEL_349d7'
        diagnostics = assemble_reference_diagnostics(ROOT)
        try:
            binding = profile(profile_id='n2:genuine:profile:' + sentinel)
            model = StateModel(binding, canonical_binding(), diagnostics.assessment_capture(),
                               normalization_capture=diagnostics.normalization_capture())
            diagnosis = model.diagnose(ash(self.g1), diagnostic_context=context('n2:genuine:n1:' + sentinel))
            self.assertIs(type(diagnosis), sv.StateDiagnosis)
            self.assertEqual(diagnostics.complete_assessment(diagnosis).status, 'COMPLETE')
            plan = model.plan_normalization(diagnosis, plan_reference='n2:genuine:n1:plan:' + sentinel,
                                            evidence_reference='n2:genuine:n1:proof:' + sentinel,
                                            policy_binding=normalization_policy())
            normalized = model.apply_normalization(plan, normalization_context=nv.NormalizationContext(
                'n2:genuine:n1:operation:' + sentinel, 'n2:genuine:n1:computation:' + sentinel,
                'n2:genuine:n1:post:' + sentinel))
            self.assertEqual(normalized.outcome, 'NORMALIZED')
            self.assertEqual(number(normalized.actual_state), 0)
            self.assertEqual(diagnostics.complete_normalization(normalized).status, 'COMPLETE')
            certificate_model = StateModel(binding, canonical_binding(), RecordingDiagnosticCapture())
            cases = [('normalize', self.g1, False, False, False, False, 'RECOVERED_VALUE'),
                     ('correct', self.g1, True, False, False, False, 'RECOVERED_VALUE'),
                     ('fallback', 1, False, True, False, False, 'RECOVERED_FALLBACK_VALUE'),
                     ('stable', 0, False, False, False, False, 'NO_ACTION'),
                     ('contained', 0, False, False, False, True, 'HANDOFF_REQUIRED'),
                     ('halt', 0, False, False, True, False, 'HANDOFF_REQUIRED'),
                     ('failed', 1, False, False, False, False, 'HANDOFF_REQUIRED')]
            for name, original, known, fallback, halt, contained, outcome in cases:
                with self.subTest(route=name):
                    origin = assessment(model, ash(original), reference='n2:genuine:' + name + ':origin:' + sentinel,
                                        known=known, fallback=fallback, halt=halt, contained=contained)
                    origin_completion = diagnostics.complete_assessment(origin)
                    self.assertEqual(origin_completion.status, 'COMPLETE')
                    entries, values = entries_for((2, 1, 1)) if fallback else ((), {})
                    entries = tuple(dataclasses.replace(entry, notes=(sentinel,)) for entry in entries)
                    actual_registry = registry(certificate_model, entries)
                    correction = CorrectionProvider(dataclasses.replace(
                        known_correction(origin, (self.g2, self.g1 ^ self.g2), 0), reason=sentinel) if known else None)
                    resolver, evaluator, post = NormalizationResolver(model), Conditions(values), PostFacts(binding)
                    engine = RecoveryEngine(model, actual_registry, diagnostics, resolver, correction, evaluator, post)
                    result = engine.recover(origin, operation_context=operation(
                        origin, 'n2:genuine:' + name + ':operation:' + sentinel))
                    self.assertEqual(result.outcome, outcome)
                    self.assertEqual(result.completion_observation.status, 'COMPLETE')
                    self.assertFalse(result.session_effects_performed)
                    if outcome in ('RECOVERED_VALUE', 'RECOVERED_FALLBACK_VALUE', 'NO_ACTION'):
                        self.assertEqual(number(result.candidate_state), 0)
                    if fallback:
                        self.assertEqual([attempt.result for attempt in result.policy_attempts], ['VALIDATION_FAILED', 'RECOVERED'])
                    if halt:
                        self.assertEqual(len(result.emitted_diagnostics), 1)
                        self.assertEqual(result.emitted_diagnostics[0].envelope.stage, 'DETECTION')
                        self.assertIsNone(result.emitted_diagnostics[0].envelope.parent_diagnostic_reference)
                    else:
                        self.assert_chain(result)
            health_observation = diagnostics.health()
            self.assertEqual(health_observation.storage_state, 'PROTECTED_VERIFIED')
            self.assertEqual(health_observation.active_reservations, 0)
            self.assertEqual(health_observation.lost_count, 0)
            self.assertIsNone(health_observation.last_failure_code)
            snapshot = diagnostics.snapshot(bundle_reference='n2:genuine:bundle:' + sentinel)
            export = diagnostics.export_pair(snapshot)
            self.assertIs(type(export), dv.ExportReceipt)
            self.assertEqual(export.status, 'COMPLETE')
            json_bytes = (diagnostics.store.root / 'diagnostics.json').read_bytes()
            markdown_bytes = (diagnostics.store.root / 'diagnostics.md').read_bytes()
            serialized = json.loads(json_bytes)
            appendix = re.search(rb'```json\n(.*?)\n```', markdown_bytes, re.S)
            self.assertIsNotNone(appendix)
            self.assertEqual(json.loads(appendix.group(1)), serialized)
            self.assertEqual(serialized, snapshot.to_record())
            for path in diagnostics.store.root.iterdir():
                if path.is_file():
                    self.assertNotIn(sentinel.encode('ascii'), path.read_bytes(), path.name)
            limitations = {entry.code for entry in snapshot.limitations}
            self.assertIn('NATIVE_COMPOSITION_DEFERRED', limitations)
            self.assertIn('NO_PHYSICAL_CRASH_PROOF', limitations)
            self.assertGreater(snapshot.redaction.field_count, 0)
            self.assertGreater(snapshot.redaction.reference_count, 0)
        finally:
            diagnostics.store.close()

    @unittest.skipUnless(os.name == "nt", "Actual adopted protected storage is Windows-specific")
    def test_genuine_collector_refuses_detached_and_mutated_origin_without_recovery_effects(self):
        from scripts.reference_diagnostics_host import assemble_reference_diagnostics
        diagnostics = assemble_reference_diagnostics(ROOT)
        try:
            binding = profile()
            actual_model = StateModel(binding, canonical_binding(), diagnostics.assessment_capture())
            detached_model = StateModel(binding, canonical_binding(), RecordingDiagnosticCapture())
            detached = assessment(detached_model, ash(self.g1), reference='n2:genuine:detached')
            resolver, provider, evaluator, post = NormalizationResolver(actual_model), CorrectionProvider(), Conditions(), PostFacts(binding)
            engine = RecoveryEngine(actual_model, registry(detached_model), diagnostics, resolver, provider, evaluator, post)
            self.assertEqual(actual_model.validate_assessment(detached).status, 'VERIFIED')
            result = engine.recover(detached, operation_context=operation(detached, 'n2:genuine:detached:operation'))
            self.assertEqual(result.failure_detail.failure_code, 'CAPTURE_ADMISSION_REJECTED')
            self.assert_no_value_effects(result)
            self.assertEqual(result.emitted_diagnostics, ())
            self.assertEqual((resolver.calls, provider.calls, evaluator.calls, post.calls), ([], [], [], []))
            original = assessment(actual_model, ash(self.g1), reference='n2:genuine:attached')
            self.assertEqual(diagnostics.complete_assessment(original).status, 'COMPLETE')
            notes = ('A semantically harmless but unacknowledged changed owned diagnostic.',)
            diagnosis = dataclasses.replace(original.state_validity_diagnostic, notes=notes)
            detection = dataclasses.replace(original.emitted_diagnostics[0], envelope=dataclasses.replace(
                original.emitted_diagnostics[0].envelope, notes=notes))
            mutated = dataclasses.replace(original, state_validity_diagnostic=diagnosis,
                                           emitted_diagnostics=(detection, original.emitted_diagnostics[1]))
            self.assertEqual(actual_model.validate_assessment(mutated).status, 'VERIFIED')
            result = engine.recover(mutated, operation_context=operation(mutated, 'n2:genuine:mutated:operation'))
            self.assertEqual(result.failure_detail.failure_code, 'CAPTURE_ADMISSION_REJECTED')
            self.assert_no_value_effects(result)
            self.assertEqual(result.emitted_diagnostics, ())
            self.assertEqual((resolver.calls, provider.calls, evaluator.calls, post.calls), ([], [], [], []))
        finally:
            diagnostics.store.close()


class RecoveryWireTests(unittest.TestCase):
    setUp = RecoveryIntegrationTests.setUp
    fixture = RecoveryIntegrationTests.fixture

    @classmethod
    def setUpClass(cls):
        cls.retrievals = []
        def deny(uri):
            cls.retrievals.append(uri)
            raise AssertionError('Recovery schemas must resolve locally: ' + uri)
        names = ('m3_state_assessment_schema.json', 'm3_normalization_plan_schema.json',
                 'm3_state_normalization_schema.json', 'm3_recovery_value_schema.json',
                 'm3_fallback_registry_schema.json', 'm3_reference_diagnostic_bundle_schema.json')
        schemas = [json.loads((ROOT / 'data/schemas' / name).read_text(encoding='utf-8')) for name in names]
        for schema in schemas:
            Draft202012Validator.check_schema(schema)
        registry = Registry(retrieve=deny).with_resources((schema['$id'], Resource.from_contents(schema)) for schema in schemas)
        cls.validators = {schema['$id'].rsplit('/', 1)[1]: Draft202012Validator(schema, registry=registry) for schema in schemas}
        cls.authored = json.loads((ROOT / 'examples/core_state_recovery/recovery_cases.example.json').read_text(encoding='utf-8'))
        cls.authored_registries = json.loads((ROOT / 'examples/core_state_recovery/fallback_registry_cases.example.json').read_text(encoding='utf-8'))

    def validator_for(self, packet):
        return self.validators[packet['schema_ref'].rsplit('/', 1)[1]]

    def assert_wire_valid(self, packet, validator=None):
        validator = self.validator_for(packet) if validator is None else validator
        errors = list(validator.iter_errors(packet))
        self.assertEqual([], [(error.validator, tuple(error.absolute_path)) for error in errors])
        self.assertEqual([], self.retrievals)

    def assert_wire_rejected(self, packet, keyword, path, validator=None):
        validator = self.validator_for(packet) if validator is None else validator
        errors = list(validator.iter_errors(packet))
        self.assertTrue(errors, 'An intended structural rejection escaped')
        def witnesses(error):
            result = {(error.validator, tuple(error.absolute_path))}
            for child in error.context:
                result |= witnesses(child)
            return result
        observed = set().union(*(witnesses(error) for error in errors))
        self.assertIn((keyword, path), observed)
        self.assertEqual([], self.retrievals)

    def test_authored_recovery_and_registry_arrays_match_literal_source_author_and_validate_offline(self):
        expected, registries = authored_wire_cases()
        self.assertEqual(expected, self.authored)
        self.assertEqual(registries, self.authored_registries)
        self.assertEqual(13, len(self.authored))
        self.assertEqual(3, len(self.authored_registries))
        self.assertEqual({'NO_ACTION', 'RECOVERED_VALUE', 'RECOVERED_FALLBACK_VALUE', 'HANDOFF_REQUIRED', 'FAILURE'},
                         {p['outcome'] for p in self.authored})
        for name, packets in (('recovery', self.authored), ('registry', self.authored_registries)):
            for index, packet in enumerate(packets):
                with self.subTest(array=name, pointer='/' + str(index)):
                    self.assert_wire_valid(packet)
        after = self.authored[12]
        self.assertEqual(after['origin_assessment']['system_state_class'], 'CORRECTABLE')
        self.assertEqual(after['route_authorization']['active_recovery_category'], 'FALLBACK_REQUIRED')
        self.assertEqual({a['diagnostic']['recovery_category'] for a in after['action_decisions']}, {'APPLY_CORRECTION'})
        self.assertEqual(self.authored[9]['failure_detail']['failure_code'], 'STEP_CAPTURE_REJECTED')
        self.assertEqual(self.authored[9]['failure_detail']['completion_failure_code'], 'COMPLETION_REJECTED')
        self.assertNotEqual(self.authored[4]['registry_snapshot']['availability'], self.authored[5]['registry_snapshot']['availability'])

    def test_actual_recovery_packets_validate_all_routes_and_capture_completion_failures(self):
        packets = []
        cases = [(0, False, False, False, False), (self.g1, False, False, False, False),
                 (self.g1, True, False, False, False), (1, False, True, False, False),
                 (1, False, False, False, False), (0, False, False, False, True), (0, False, False, True, False)]
        for original, known, fallback, halt, contained in cases:
            _, origin, engine, *_ = self.fixture(original=original, known=known, fallback=fallback, halt=halt, contained=contained)
            packets.append(engine.recover(origin, operation_context=operation(origin)).to_record())
        for completion in ('INCOMPLETE', 'NONE', 'WRONG_REFERENCE', 'THROW'):
            diagnostics = ControlledDiagnostics(completion=completion)
            _, origin, engine, *_ = self.fixture(diagnostics=diagnostics)
            packets.append(engine.recover(origin, operation_context=operation(origin)).to_record())
        for mode in ('REJECTED', 'NOT_CONFIRMED', 'NONE', 'WRONG_REFERENCE', 'THROW_BEFORE', 'THROW_AFTER'):
            diagnostics = ControlledDiagnostics(fail=lambda record: record.record_kind == 'ACTION_VALUE_COMPUTED' and
                record.payload.action == 'NORMALIZE_XOR', mode=mode)
            _, origin, engine, *_ = self.fixture(diagnostics=diagnostics)
            packets.append(engine.recover(origin, operation_context=operation(origin)).to_record())
        for status in ('REJECTED', 'NOT_CONFIRMED'):
            diagnostics = ControlledDiagnostics(post_capture=status)
            _, origin, engine, *_ = self.fixture(diagnostics=diagnostics)
            packets.append(engine.recover(origin, operation_context=operation(origin)).to_record())
        entries, values = entries_for((2, 1, 1))
        _, origin, engine, *_ = self.fixture(original=1, fallback=True, entries=entries, conditions=Conditions(values))
        packets.append(engine.recover(origin, operation_context=operation(origin)).to_record())
        _, origin, engine, _, _, provider, *_ = self.fixture(known=True)
        provider.result = known_correction(origin, (self.g1, self.g2, self.g2), 0)
        packets.append(engine.recover(origin, operation_context=operation(origin)).to_record())
        _, origin, engine, *_ = self.fixture(norm='UNAVAILABLE')
        packets.append(engine.recover(origin, operation_context=operation(origin)).to_record())
        self.assertEqual(22, len(packets))
        for index, packet in enumerate(packets):
            with self.subTest(actual_packet=index):
                self.assert_wire_valid(packet)
        for snapshot in (registry(StateModel(profile(), canonical_binding(), RecordingDiagnosticCapture()), entries).snapshot,
                         registry(StateModel(profile(), canonical_binding(), RecordingDiagnosticCapture())).snapshot,
                         registry(StateModel(profile(), canonical_binding(), RecordingDiagnosticCapture()), unavailable=True).snapshot):
            self.assert_wire_valid(snapshot.to_record())

    def test_recovery_wire_mutations_have_exact_owned_keyword_and_location(self):
        stable, corrected, fallback, failed, capture, normalized = [self.authored[i] for i in (0, 1, 2, 3, 9, 11)]
        mutations = [('extra-root', stable, lambda p: p.update(unowned=True), 'additionalProperties', ()),
                     ('false-session-effect', stable, lambda p: p.update(session_effects_performed=True), 'const', ('session_effects_performed',)),
                     ('wrong-scope', stable, lambda p: p.update(execution_scope='OPERATIONAL_SESSION'), 'const', ('execution_scope',))]
        for field in stable:
            mutations.append(('missing-' + field, stable, lambda p, f=field: p.pop(f), 'required', ()))
        mutations.extend([
            ('boolean-bit', corrected, lambda p: p['steps'][1]['codeword']['bits'].__setitem__(0, True), 'type', ('steps', 1, 'codeword', 'bits', 0)),
            ('noncanonical-executed-word', corrected, lambda p: p['steps'][1]['codeword'].update(bits=[0] * 8 + [1]), 'enum', ('steps', 1, 'codeword', 'bits')),
            ('bool-index', corrected, lambda p: p['steps'][0].update(step_index=False), 'type', ('steps', 0, 'step_index')),
            ('step-769', corrected, lambda p: p.update(steps=p['steps'] * 257), 'maxItems', ('steps',)),
            ('post-34', corrected, lambda p: p.update(post_assessments=p['post_assessments'] * 34), 'maxItems', ('post_assessments',)),
            ('decision-36', corrected, lambda p: p.update(action_decisions=p['action_decisions'] * 36), 'maxItems', ('action_decisions',)),
            ('canonical-step-33', corrected, lambda p: p['action_decisions'][0]['diagnostic'].update(steps=p['action_decisions'][0]['diagnostic']['steps'] * 11), 'maxItems', ('action_decisions', 0, 'diagnostic', 'steps')),
            ('fake-pending-outcome', corrected, lambda p: p['action_decisions'][0]['diagnostic'].update(outcome='PENDING'), 'enum', ('action_decisions', 0, 'diagnostic', 'outcome')),
            ('lost-correction-proof', corrected, lambda p: p.update(correction_observation=None), 'type', ('correction_observation',)),
            ('lost-normalization-proof', normalized, lambda p: p.update(normalization_preparation=None), 'type', ('normalization_preparation',)),
            ('normalization-incomplete-T', normalized, lambda p: p['normalization_preparation']['plan'].update(eligible_targets_complete=False), 'const', ('normalization_preparation', 'plan', 'eligible_targets_complete')),
            ('known-chain-17', corrected, lambda p: p['correction_observation']['submitted'].update(chain=p['correction_observation']['submitted']['chain'] * 17), 'maxItems', ('correction_observation', 'submitted', 'chain')),
            ('foreign-source-pin', corrected, lambda p: p['source_binding']['contract_pins'][0].update(sha256='0' * 64), 'const', ('source_binding', 'contract_pins', 0)),
            ('missing-eight-field-envelope', corrected, lambda p: p['emitted_diagnostics'][0]['envelope'].pop('chain_root_reference'), 'required', ('emitted_diagnostics', 0, 'envelope')),
            ('new-N3-rule', corrected, lambda p: p['emitted_diagnostics'][0]['envelope'].update(rule_ids=['ASH-SAFE-HALT-FINALITY-001']), 'enum', ('emitted_diagnostics', 0, 'envelope', 'rule_ids', 0)),
            ('terminal-claim', corrected, lambda p: p['emitted_diagnostics'][0]['envelope'].update(disposition='TERMINAL'), 'enum', ('emitted_diagnostics', 0, 'envelope', 'disposition')),
            ('fallback-summary-no-policy', fallback, lambda p: p['action_decisions'][-1]['diagnostic'].update(fallback_policy_id=None), 'type', ('action_decisions', 1, 'diagnostic', 'fallback_policy_id')),
            ('unknown-failure', capture, lambda p: p['failure_detail'].update(failure_code='RECOVERY_FAILED'), 'enum', ('failure_detail', 'failure_code')),
            ('capture-complete-status', capture, lambda p: p['failure_detail'].update(capture_status='COMPLETE'), 'enum', ('failure_detail', 'capture_status')),
            ('handoff-claims-entry', failed, lambda p: p['directive'].update(actual_mode_status='ENTERED'), 'const', ('directive', 'actual_mode_status')),
            ('made-up-trigger', failed, lambda p: p['directive'].update(trigger='FAILED'), 'enum', ('directive', 'trigger')),
        ])
        for name, base, mutate, keyword, path in mutations:
            with self.subTest(case=name):
                altered = copy.deepcopy(base); mutate(altered)
                self.assert_wire_rejected(altered, keyword, path, self.validator_for(base))
        # Declarations deliberately admit exact full-width nonmembers. Actual
        # replay above rejects them and pure StateModel proof tests check C.
        declared = copy.deepcopy(corrected['correction_observation']['submitted'])
        declared['chain'] = [{'state_space': 'F2^9', 'bits': [0] * 8 + [1]}]
        owner = self.validators['m3_recovery_value_schema.json']
        self.assert_wire_valid(declared, owner.evolve(schema={'$ref': owner.schema['$id'] + '#/$defs/KnownCorrection'}))

    def test_registry_wire_bounds_closure_and_declared_provenance_have_exact_witnesses(self):
        available, empty, unavailable = self.authored_registries
        mutations = [('extra-root', available, lambda p: p.update(system_state_class='STABLE'), 'additionalProperties', ()),
            ('unavailable-invents-entries', unavailable, lambda p: p.update(entries=[]), 'additionalProperties', ()),
            ('available-33', available, lambda p: p.update(entries=p['entries'] * 33), 'maxItems', ('entries',)),
            ('rank-bool', available, lambda p: p['entries'][0].update(ordering_rank=True), 'type', ('entries', 0, 'ordering_rank')),
            ('rank-low', available, lambda p: p['entries'][0].update(ordering_rank=-(1 << 63) - 1), 'minimum', ('entries', 0, 'ordering_rank')),
            ('rank-high', available, lambda p: p['entries'][0].update(ordering_rank=(1 << 63)), 'maximum', ('entries', 0, 'ordering_rank')),
            ('zero-policy', available, lambda p: p['entries'][0].update(policy_id='FALLBACK-STATE-000'), 'pattern', ('entries', 0, 'policy_id')),
            ('nine-conditions', available, lambda p: p['entries'][0].update(applicability_conditions=[{'condition_id': 'condition', 'source_binding': p['source_binding']['source_binding']}] * 9), 'maxItems', ('entries', 0, 'applicability_conditions')),
            ('empty-notes', available, lambda p: p['entries'][0].update(notes=[]), 'minItems', ('entries', 0, 'notes')),
            ('assert-authenticated', available, lambda p: p['source_binding'].update(source_verification='AUTHENTICATED'), 'const', ('source_binding', 'source_verification')),
            ('lost-certification', available, lambda p: p.update(candidate_certifications=[]), 'minItems', ('candidate_certifications',)),
        ]
        for field in available:
            mutations.append(('missing-' + field, available, lambda p, f=field: p.pop(f), 'required', ()))
        for name, base, mutate, keyword, path in mutations:
            with self.subTest(case=name):
                altered = copy.deepcopy(base); mutate(altered)
                self.assert_wire_rejected(altered, keyword, path, self.validator_for(base))
        self.assert_wire_valid(empty)
        self.assert_wire_valid(unavailable)

    def test_recovery_envelope_summary_all_ten_separators_and_exact_512_bound(self):
        base = self.authored[1]; owner = self.validator_for(base)
        path = ('emitted_diagnostics', 0, 'envelope', 'summary')
        for separator in ('\n', '\r', '\v', '\f', '\x1c', '\x1d', '\x1e', '\x85', '\u2028', '\u2029'):
            with self.subTest(separator=ord(separator)):
                altered = copy.deepcopy(base); altered['emitted_diagnostics'][0]['envelope']['summary'] = 'before' + separator + 'after'
                self.assert_wire_rejected(altered, 'not', path, owner)
        for summary in ('x' * 512, 'plain space and\ttab'):
            altered = copy.deepcopy(base); altered['emitted_diagnostics'][0]['envelope']['summary'] = summary
            self.assert_wire_valid(altered, owner)
        altered = copy.deepcopy(base); altered['emitted_diagnostics'][0]['envelope']['summary'] = 'x' * 513
        self.assert_wire_rejected(altered, 'maxLength', path, owner)


if __name__ == '__main__':
    unittest.main()

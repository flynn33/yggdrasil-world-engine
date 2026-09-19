#!/usr/bin/env python3
"""Reproduce a bounded compatibility review; never modify engine source.

An expected incompatibility is a reproduced finding, not product acceptance.
Use a checkout or verified file extraction containing the pinned source files.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
from itertools import product
import json
from pathlib import Path
import platform
import sys
import unittest

BASELINE_COMMIT = '2db1230f638cd065d791c05f1adb7b4b51505c57'
PLANNING_COMMIT = '4b5e7b9a5428df37491bec1b820074054b4fef90'
BASELINE_FILES = {
    'core/ash_pattern_engine/ash_canonical.py': '1d7f34f03747f494542ce9594d3ec955ae892942',
    'core/ash_pattern_engine/__init__.py': 'f46f3264c323aa741eb4968c2a42e641ed2c44fe',
    'tests/test_ash_canonical.py': '135975db2f8b703acaaf90175403793bd143139f',
}
CANDIDATE_FILES = {
    'verification/value_model.py': 'bc85a5735174f93a5552607dff3be71fca0eb3d1',
    'schemas/ash-values.candidate.schema.json': 'd68bc368615721680809bb8e2003ae30c998b7bb',
}


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def encoded(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('utf-8')


def blob(path: Path) -> str:
    require(path.is_file() and not path.is_symlink(), f'Not an ordinary source file: {path}')
    data = path.read_bytes()
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def check_sources(root: Path, sources: dict[str, str]) -> dict[str, str]:
    actual = {name: blob(root / name) for name in sources}
    require(actual == sources, 'Pinned source mismatch; no source module was executed.')
    return actual


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, 'Cannot load inspected source.')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class CompatibilityReview:
    def __init__(self, baseline: Path, candidate: Path) -> None:
        self.baseline, self.candidate = baseline, candidate
        self.before = {'baseline': check_sources(baseline, BASELINE_FILES),
                       'candidate': check_sources(candidate, CANDIDATE_FILES)}
        self.old = load('ywe_compatibility_baseline', baseline / next(iter(BASELINE_FILES)))
        self.new = load('ywe_compatibility_candidate', candidate / 'verification/value_model.py')
        self.codec = self.new.JsonValueCodec

    def values(self) -> dict:
        require(self.old.CANONICAL_CODEWORDS == self.new.CODEWORD_BITS, 'Codeword enumeration changed.')
        cases = 0
        for bits in product((0, 1), repeat=9):
            value = self.codec.state({'state_space': 'F2^9', 'bits': list(bits)})
            require(value.bits == self.old.normalize_bits(bits), 'Valid state changed.')
            for word in self.new.CODEWORD_BITS:
                expected = self.old.transform_state(bits, word).signature
                actual = value.transformed_by(self.new.CanonicalCodeword(word)).signature()
                require(actual == expected, 'Valid transformation changed.')
                cases += 1
        return {'represented_states': 512, 'matching_codewords': 16,
                'matching_transformations': cases}

    def outputs(self) -> dict:
        sequences = ([], ['000000000'], ['000011110', '000011110'],
                     ['000011110', '001100110', '000011110'])
        digest = hashlib.sha256()
        comparisons = 0
        for bits in product((0, 1), repeat=9):
            signature = ''.join(map(str, bits))
            for sequence in sequences:
                state = self.codec.state_signature(signature)
                words = self.codec.codeword_sequence(sequence)
                # Verification-only boundary experiment: same existing helper,
                # explicit checked values. Not an independent semantics oracle.
                operands = tuple(w.bits for w in words)
                old_snapshot = self.old.build_cosmic_pattern_snapshot(signature, sequence)
                checked_snapshot = self.old.build_cosmic_pattern_snapshot(state.bits, iter(operands))
                old_plan = self.old.plan_generation('compatibility-review', signature, sequence)
                checked_plan = self.old.plan_generation('compatibility-review', state.bits, iter(operands))
                for expected, actual in ((old_snapshot, checked_snapshot), (old_plan, checked_plan)):
                    require(encoded(actual) == encoded(expected), 'Whole helper packet changed.')
                    digest.update(encoded(actual) + b'\n')
                    comparisons += 1
                require(checked_snapshot['active_codeword_sequence'] == sequence, 'Sequence changed.')
                require(checked_snapshot['state_identity'] == checked_snapshot['realm_identity'], 'Alias changed.')
                require(checked_plan['source_state_identity'] == checked_plan['source_realm'], 'Source alias changed.')
                require(checked_plan['destination_state_identity'] == checked_plan['destination_realm'], 'Target alias changed.')
        return {'seed_count': 512, 'ordered_sequences_per_seed': len(sequences),
                'snapshot_comparisons': comparisons // 2, 'plan_comparisons': comparisons // 2,
                'comparison_encoding': 'sorted-key compact JSON for this experiment only; not a wire standard',
                'packet_digest_sha256': digest.hexdigest(), 'differences': 0}

    def boundaries(self) -> dict:
        probes = [
            ('integer-array', [1] + [0] * 8, True, True),
            ('exact-integral-number', [1.0] + [0] * 8, True, True),
            ('ninth-state-bit', [0] * 8 + [1], True, True),
            ('short-array', [0] * 8, False, False),
            ('long-array', [0] * 10, False, False),
            ('integer-two', [2] + [0] * 8, False, False),
            ('null-bit', [None] + [0] * 8, False, False),
            ('fraction-below-one', [0.9] + [0] * 8, True, False),
            ('fraction-above-one', [1.9] + [0] * 8, True, False),
            ('negative-fraction', [-0.1] + [0] * 8, True, False),
            ('boolean-bit', [True] + [0] * 8, True, False),
            ('string-bit', ['1'] + [0] * 8, True, False),
            ('ascii-signature', '100000000', True, True),
            ('padded-signature', ' 100000000 ', True, False),
            ('unicode-signature', '\u066100000000', True, False),
        ]
        rows = []
        for name, value, old_ok, new_ok in probes:
            row = {'case': name, 'input': value}
            for label, operation, expected in (
                ('baseline', lambda: self.old.normalize_bits(deepcopy(value)), old_ok),
                ('candidate', lambda: (self.codec.state_signature(value) if type(value) is str
                                      else self.codec.state({'state_space': 'F2^9', 'bits': deepcopy(value)})).bits, new_ok),
            ):
                try:
                    result = operation()
                    row[label] = {'accepted': True, 'bits': list(result)}
                except (ValueError, TypeError, OverflowError) as exc:
                    row[label] = {'accepted': False, 'error': getattr(exc, 'code', type(exc).__name__)}
                require(row[label]['accepted'] == expected, f'Unexpected outcome: {name}/{label}')
            rows.append(row)
        return {'probe_count': len(rows), 'acceptance_differences': sum(
                row['baseline']['accepted'] != row['candidate']['accepted'] for row in rows), 'cases': rows}

    def ownership(self) -> dict:
        supplied = [1] + [0] * 8
        old = self.old.AshState(supplied)
        new = self.codec.state({'state_space': 'F2^9', 'bits': supplied})
        before = old.signature
        supplied[0] = 0
        require(old.signature != before, 'Expected baseline direct-constructor aliasing not reproduced.')
        require(new.signature() == before, 'Candidate retained a mutable array.')
        unchecked = self.old.AshState((0, 1))
        try:
            self.new.AshState((0, 1))
        except self.new.ContractError as exc:
            require(exc.code == 'BIT_WIDTH', 'Wrong candidate rejection.')
        else:
            raise AssertionError('Candidate accepted short direct construction.')
        return {'baseline_caller_mutation_changes_direct_object': True,
                'candidate_caller_mutation_changes_object': False,
                'baseline_short_direct_construction_succeeds': len(unchecked.bits) == 2,
                'candidate_short_direct_construction_rejected': True,
                'signature_api': {'baseline': 'property', 'candidate': 'method'},
                'interpretation': 'Direct-constructor risk reproduced. No claim that a shipped caller uses this route.'}

    def schema_binding(self) -> dict:
        from jsonschema import Draft202012Validator
        schema = json.loads((self.candidate / 'schemas/ash-values.candidate.schema.json').read_text())
        root = Draft202012Validator(schema)
        typed_schema = deepcopy(schema)
        typed_schema.pop('oneOf')
        typed_schema['$ref'] = '#/$defs/CanonicalCodewordRecord'
        typed = Draft202012Validator(typed_schema)
        record = {'state_space': 'F2^9', 'bits': [0] * 9}
        require(root.is_valid(record) and not typed.is_valid(record), 'Expected-type ambiguity not reproduced.')
        extended = dict(record, note='consumer metadata')
        require(not root.is_valid(extended), 'Closed-record rule unexpectedly changed.')
        codeword = dict(record, membership=True)
        require(typed.is_valid(codeword), 'Typed codeword example failed.')
        signature = self.old.build_cosmic_pattern_snapshot('100000000', ['000011110'])['active_codeword_sequence'][0]
        self.codec.codeword_signature(signature)
        return {'root_accepts_state_where_codeword_was_expected': True,
                'typed_codeword_target_rejects_missing_membership': True,
                'typed_codeword_target_accepts_actual_member_with_assertion': True,
                'additional_record_member_rejected': True,
                'existing_codeword_sequence_signature_needs_no_membership_member': True,
                'limit': 'Standalone record policy is not applied to complete snapshots or envelopes.'}

    def legacy_tests(self) -> dict:
        # Preserve the existing test file exactly. Run only its four tests.
        sys.path.insert(0, str(self.baseline))
        try:
            suite = unittest.defaultTestLoader.discover(str(self.baseline / 'tests'), pattern='test_ash_canonical.py')
            text = io.StringIO()
            result = unittest.TextTestRunner(stream=text, verbosity=2).run(suite)
            require(result.testsRun == 4 and result.wasSuccessful(), 'Pinned identity regression failed.')
            return {'tests_run': result.testsRun, 'failures': len(result.failures),
                    'errors': len(result.errors), 'successful': result.wasSuccessful()}
        finally:
            sys.path.pop(0)

    def run(self) -> dict:
        results = {name: getattr(self, name)() for name in
                   ('values', 'outputs', 'boundaries', 'ownership', 'schema_binding', 'legacy_tests')}
        require(self.before['baseline'] == check_sources(self.baseline, BASELINE_FILES), 'Baseline source changed.')
        require(self.before['candidate'] == check_sources(self.candidate, CANDIDATE_FILES), 'Candidate source changed.')
        return {'review_id': 'YWE-M2-COMPATIBILITY-20260919',
                'baseline_commit': BASELINE_COMMIT, 'planning_parent_commit': PLANNING_COMMIT,
                'executed_at': datetime.now(timezone.utc).isoformat(),
                'environment': {'python': platform.python_version(), 'platform': platform.system()},
                'source_blob_verification': self.before, 'source_preserved': True,
                'review_checks_passed': True, 'compatibility_verdict': 'not_drop_in_compatible',
                'results': results, 'results_sha256': hashlib.sha256(encoded(results)).hexdigest(),
                'limits': ['verified selected-file extraction, not a full checkout',
                           'no complete consumer inventory or full repository suite',
                           'existing packet helper reused; not an independent semantics oracle',
                           'no active source, production schema, candidate approval or milestone changed']}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-root', required=True, type=Path)
    parser.add_argument('--candidate-root', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.report.exists():
            raise FileExistsError('Refusing to overwrite an existing report.')
        report = CompatibilityReview(args.baseline_root.resolve(), args.candidate_root.resolve()).run()
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open('x', encoding='utf-8') as output:
            json.dump(report, output, indent=2, ensure_ascii=True, allow_nan=False)
            output.write('\n')
        print('Compatibility findings reproduced; not a drop-in-compatible replacement.')
        print(report['results_sha256'])
        return 0
    except Exception as exc:
        print(f'Review incomplete: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

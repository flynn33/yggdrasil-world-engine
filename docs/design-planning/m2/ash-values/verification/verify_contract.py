#!/usr/bin/env python3
"""Run source-bound candidate checks. Does not edit a product checkout."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from importlib.metadata import version
from itertools import product
import json
import platform
from pathlib import Path
import sys
from typing import Any, Callable

from jsonschema import Draft202012Validator, validators
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from value_model import (AshState, CanonicalCodeword, CODEWORD_BITS,
                         CODEWORD_SIGNATURES, ContractError, JsonValueCodec)


def integer_type(checker: Any, value: Any) -> bool:
    """Bridge exact-decimal JSON parser values to standard integer semantics."""
    if type(value) is Decimal:
        return value.is_finite() and value == value.to_integral_value()
    return Draft202012Validator.TYPE_CHECKER.is_type(value, 'integer')


ExactJsonValidator = validators.extend(
    Draft202012Validator,
    type_checker=Draft202012Validator.TYPE_CHECKER.redefine('integer', integer_type),
)


def pointer(path: Any) -> str:
    return ''.join('/' + str(x).replace('~', '~0').replace('/', '~1') for x in path)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class ContractVerification:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.schema = self.read('schemas/ash-values.candidate.schema.json')
        self.uri = self.schema['$id']
        self.fixtures = self.read('fixtures/instances.json')
        self.cases = self.read('fixtures/catalog.json')['cases']
        self.code_source = self.read('fixtures/pinned-codewords.json')
        self.results: list[dict[str, Any]] = []
        self.network_requests: list[str] = []
        self.registry = Registry(retrieve=self.deny_retrieval).with_resource(
            self.uri, Resource.from_contents(self.schema))

    def read(self, name: str) -> Any:
        return json.loads((self.root / name).read_text(encoding='utf-8'))

    def deny_retrieval(self, uri: str) -> Any:
        self.network_requests.append(uri)
        raise NoSuchResource(ref=uri)

    def validator(self, ref: str, schema: Any = None) -> Any:
        if schema is None:
            registry = self.registry
        else:
            registry = Registry(retrieve=self.deny_retrieval).with_resource(
                self.uri, Resource.from_contents(schema))
        return ExactJsonValidator({'$ref': ref}, registry=registry)

    def group(self, name: str, test: Callable[[], dict[str, Any]]) -> None:
        try:
            self.results.append({'group': name, 'status': 'pass', **test()})
        except Exception as exc:
            self.results.append({'group': name, 'status': 'fail',
                                 'error_type': type(exc).__name__, 'message': str(exc)})

    def meta_and_catalog(self) -> dict[str, Any]:
        Draft202012Validator.check_schema(self.schema)
        for definition in self.schema['$defs'].values():
            Draft202012Validator.check_schema(definition)
        catalog = self.read('schemas/catalog.json')['schemas']
        require(len(catalog) == 1, 'This experiment has exactly one schema resource.')
        require(catalog[0]['id'] == self.uri, 'Catalog/schema ID disagreement.')
        require(catalog[0]['path'] == 'schemas/ash-values.candidate.schema.json', 'Wrong catalog path.')
        ids = [c['id'] for c in self.cases]
        require(len(ids) == len(set(ids)), 'Duplicate fixture IDs.')
        require(set(ids) == set(self.fixtures), 'Unbound or missing fixtures.')
        for case in self.cases:
            require(case['instance_pointer'] == '/' + case['id'], 'Invalid fixture pointer.')
            require(case['instance_file'] == 'fixtures/instances.json', 'Wrong fixture file.')
            require(case['schema_ref'].split('#/$defs/')[1] in self.schema['$defs'], 'Unresolved definition.')
        return {'meta_schemas_checked': 1 + len(self.schema['$defs']),
                'bound_fixtures': len(ids)}

    @staticmethod
    def decode_target(target: str, value: Any) -> Any:
        decoders = {'AshStateRecord': JsonValueCodec.state,
                    'CanonicalCodewordRecord': JsonValueCodec.codeword,
                    'StateSignature': JsonValueCodec.state_signature,
                    'CodewordSignature': JsonValueCodec.codeword_signature,
                    'CanonicalCodewordSequence': JsonValueCodec.codeword_sequence}
        return decoders[target](value)

    def fixture_checks(self) -> dict[str, Any]:
        outcomes = []
        for case in self.cases:
            value = self.fixtures[case['id']]
            errors = sorted(self.validator(case['schema_ref']).iter_errors(value),
                            key=lambda e: (pointer(e.absolute_path), pointer(e.absolute_schema_path), str(e.validator)))
            actual = not errors
            require(actual == case['expected_valid'], f"Schema result mismatch: {case['id']}")
            reason = case.get('expected_schema_error')
            if reason:
                require(any(e.validator == reason['keyword'] and pointer(e.absolute_path) == reason['instance_pointer']
                            for e in errors), f"Wrong rejection reason: {case['id']}")
            target = case['schema_ref'].split('#/$defs/')[1]
            failure = None
            try:
                self.decode_target(target, value)
                model_valid = True
            except ContractError as exc:
                failure = exc.as_record()
                model_valid = False
            require(model_valid == case['expected_valid'], f"Model result mismatch: {case['id']}")
            if failure:
                require(failure['code'] == case['expected_model_error'], f"Wrong model rejection: {case['id']}")
            outcomes.append({'id': case['id'], 'expected_valid': case['expected_valid'],
                             'schema_valid': actual, 'model_valid': model_valid,
                             'model_failure': failure,
                             'schema_errors': [{'keyword': e.validator,
                                                'instance_pointer': pointer(e.absolute_path),
                                                'schema_pointer': pointer(e.absolute_schema_path)} for e in errors]})
        return {'cases': len(outcomes), 'accepted_cases': sum(c['schema_valid'] for c in outcomes),
                'rejected_cases': sum(not c['schema_valid'] for c in outcomes), 'outcomes': outcomes}

    def canonical_set(self) -> dict[str, Any]:
        source = self.code_source
        require(source['ordered_signatures'] == list(CODEWORD_SIGNATURES), 'Source/model enumeration mismatch.')
        require(source['commit'] == '2db1230f638cd065d791c05f1adb7b4b51505c57', 'Wrong source pin.')
        require(source['git_blob_sha1'] == '79f9172cd14c3d1e3a42a4a5f1aedf2d88bfef7b', 'Wrong source blob.')
        generators = [int(s, 2) for s in source['generator_signatures']]
        closure = set()
        for selection in product((False, True), repeat=4):
            number = 0
            for include, generator in zip(selection, generators):
                if include:
                    number ^= generator
            closure.add(format(number, '09b'))
        require(closure == set(CODEWORD_SIGNATURES), 'Independent generator closure does not match enumeration.')
        require(len(closure) == 16, 'Wrong canonical set size.')
        for a in closure:
            for b in closure:
                require(format(int(a, 2) ^ int(b, 2), '09b') in closure, 'Not XOR closed.')
        return {'enumerated_members': 16, 'generator_combinations': 16,
                'pairwise_closure_cases': 256, 'ordered_signatures': list(CODEWORD_SIGNATURES)}

    def exhaustive_values(self) -> dict[str, Any]:
        sv = self.validator(self.uri + '#/$defs/AshStateRecord')
        cv = self.validator(self.uri + '#/$defs/CanonicalCodewordRecord')
        ss = self.validator(self.uri + '#/$defs/StateSignature')
        cs = self.validator(self.uri + '#/$defs/CodewordSignature')
        source_set = set(self.code_source['ordered_signatures'])
        stream = sha256()
        admitted = 0
        for n in range(512):
            signature = format(n, '09b')
            bits = [int(c) for c in signature]
            record = {'state_space': 'F2^9', 'bits': bits}
            require(sv.is_valid(record) and ss.is_valid(signature), f'State rejection: {signature}')
            state = JsonValueCodec.state(record)
            require(JsonValueCodec.state_signature(signature) == state, 'Signature mapping disagreement.')
            encoded = JsonValueCodec.encode(state)
            expected_bytes = ('{"state_space":"F2^9","bits":[' + ','.join(signature) + ']}').encode()
            require(encoded == expected_bytes, 'Unexpected canonical state bytes.')
            require(JsonValueCodec.state(JsonValueCodec.parse_json(encoded)) == state, 'State round-trip failed.')
            stream.update(encoded + b'\n')
            record['membership'] = True
            expected = signature in source_set
            require(cv.is_valid(record) == expected, 'Codeword schema membership mismatch.')
            require(cs.is_valid(signature) == expected, 'Codeword signature membership mismatch.')
            try:
                value = JsonValueCodec.codeword(record)
                accepted = True
            except ContractError as exc:
                require(exc.code == 'CODEWORD_MEMBERSHIP', 'Wrong nonmember error.')
                accepted = False
            require(accepted == expected, 'Codeword model membership mismatch.')
            if accepted:
                admitted += 1
                encoded = JsonValueCodec.encode(value)
                expected_bytes = ('{"state_space":"F2^9","bits":[' + ','.join(signature) + '],"membership":true}').encode()
                require(encoded == expected_bytes, 'Unexpected canonical codeword bytes.')
                require(JsonValueCodec.codeword(JsonValueCodec.parse_json(encoded)) == value, 'Codeword round-trip failed.')
                require(value.ordinal() == self.code_source['ordered_signatures'].index(signature), 'Index changed.')
                stream.update(encoded + b'\n')
        return {'state_records': 512, 'state_signatures': 512,
                'codeword_candidates': 512, 'accepted_codewords': admitted,
                'rejected_nonmembers': 512 - admitted, 'state_round_trips': 512,
                'codeword_round_trips': admitted, 'canonical_wire_corpus_sha256': stream.hexdigest()}

    def transformations(self) -> dict[str, Any]:
        stream = sha256()
        for n in range(512):
            state = AshState(tuple(int(x) for x in format(n, '09b')))
            original = state.bits
            for signature in self.code_source['ordered_signatures']:
                code = CanonicalCodeword(tuple(int(x) for x in signature))
                before = code.bits
                result = state.transformed_by(code)
                expected = format(n ^ int(signature, 2), '09b')
                require(result.signature() == expected, 'Coordinate and integer XOR disagree.')
                require(result.transformed_by(code) == state, 'Involution failed.')
                require(state.bits == original and code.bits == before, 'Input mutation.')
                require(result is not state, 'Result must be a distinct value object in this model.')
                stream.update(f'{n:03}:{signature}:{expected}\n'.encode())
        return {'state_codeword_pairs': 8192, 'involution_cases': 8192,
                'originals_unchanged_cases': 8192, 'transformation_corpus_sha256': stream.hexdigest()}

    def raw_json(self) -> dict[str, Any]:
        rows = []
        validator = self.validator(self.uri + '#/$defs/AshStateRecord')
        for case in self.read('fixtures/raw-json-cases.json')['cases']:
            parsed = False
            schema_valid = None
            failure = None
            try:
                instance = JsonValueCodec.parse_json(case['text'])
                parsed = True
                schema_valid = validator.is_valid(instance)
                value = JsonValueCodec.state(instance)
                require(JsonValueCodec.state(JsonValueCodec.parse_json(JsonValueCodec.encode(value))) == value,
                        'Raw round-trip failed.')
                valid = True
            except ContractError as exc:
                valid = False
                failure = exc.code
            require(valid == case['valid'], f"Raw-case mismatch: {case['id']}")
            if not valid:
                require(failure == case['code'], f"Raw error mismatch: {case['id']}")
            if parsed:
                require(schema_valid == valid, f"Exact JSON/schema mismatch: {case['id']}")
            rows.append({'id': case['id'], 'valid': valid, 'parsed': parsed,
                         'schema_valid': schema_valid, 'failure': failure})
        try:
            JsonValueCodec.parse_json(b'\xff')
            raise AssertionError('Invalid UTF-8 accepted.')
        except ContractError as exc:
            require(exc.code == 'JSON_SYNTAX', 'Wrong UTF-8 error.')
        try:
            JsonValueCodec.parse_json(b' ' * (JsonValueCodec.PROBE_INPUT_BYTE_LIMIT + 1))
            raise AssertionError('Probe budget not enforced.')
        except ContractError as exc:
            require(exc.code == 'PROBE_INPUT_LIMIT', 'Wrong budget error.')
        return {'raw_json_cases': len(rows), 'invalid_utf8_case': 'rejected',
                'probe_only_budget_case': 'rejected', 'outcomes': rows}

    def ownership_and_order(self) -> dict[str, Any]:
        source_list = [0] * 9
        state = JsonValueCodec.state({'state_space': 'F2^9', 'bits': source_list})
        source_list[0] = 1
        require(state.bits == (0,) * 9, 'Input alias leaked.')
        output = JsonValueCodec.state_record(state)
        output['bits'][0] = 1
        require(state.bits == (0,) * 9, 'Output alias leaked.')
        try:
            state.bits = (1,) * 9
            raise AssertionError('Frozen state was mutable.')
        except FrozenInstanceError:
            pass
        bad_domain_inputs = ([0] * 9, (0,) * 8, (True,) + (0,) * 8, (0.5,) + (0,) * 8)
        for bad in bad_domain_inputs:
            try:
                AshState(bad)
                raise AssertionError('Invalid domain construction admitted.')
            except ContractError:
                pass
        try:
            CanonicalCodeword((1,) + (0,) * 8)
            raise AssertionError('Invalid codeword constructed.')
        except ContractError as exc:
            require(exc.code == 'CODEWORD_MEMBERSHIP', 'Wrong constructor failure.')
        try:
            state.transformed_by(AshState((0,) * 9))
            raise AssertionError('Unvalidated transformation operand admitted.')
        except ContractError as exc:
            require(exc.code == 'CODEWORD_TYPE', 'Wrong operand failure.')
        sequence = [CODEWORD_SIGNATURES[2], CODEWORD_SIGNATURES[1], CODEWORD_SIGNATURES[2]]
        actual = JsonValueCodec.codeword_sequence(sequence)
        require([v.signature() for v in actual] == sequence, 'Sequence reordered/deduplicated.')
        require(JsonValueCodec.codeword_sequence([]) == (), 'Empty sequence failed.')
        zero = CanonicalCodeword((0,) * 9)
        try:
            zero.bits = (1,) * 9
            raise AssertionError('Frozen codeword was mutable.')
        except FrozenInstanceError:
            pass
        return {'checks': 12, 'scope': 'input/output aliasing, frozen fields, guarded construction, typed transform, order and duplicates'}

    def root_dispatch(self) -> dict[str, Any]:
        validator = self.validator(self.uri)
        count = 0
        for case in self.cases:
            if case['schema_ref'].endswith(('AshStateRecord', 'CanonicalCodewordRecord')):
                # A complete codeword is valid at the root even when rejected as AshState specifically.
                expected = case['expected_valid'] or case['id'] == 'state-do-not-infer-membership' or case['id'] == 'codeword-missing-membership'
                require(validator.is_valid(self.fixtures[case['id']]) == expected, f"Root dispatch: {case['id']}")
                count += 1
        return {'cases': count,
                'limitation': 'Root union admits either record; consumers requiring a codeword must use its bound schema/decoder.'}

    def mutations(self) -> dict[str, Any]:
        def remove_min(s): s['$defs']['StateBits'].pop('minItems')
        def remove_max(s): s['$defs']['StateBits'].pop('maxItems')
        def broaden_bits(s): s['$defs']['StateBits']['items']['enum'].append(2)
        def remove_membership(s): s['$defs']['CodewordBits'].pop('enum')
        def remove_space(s): s['$defs']['AshStateRecord']['properties']['state_space'].pop('const')
        def remove_required(s): s['$defs']['AshStateRecord']['required'].remove('bits')
        def allow_extra(s): s['$defs']['AshStateRecord']['additionalProperties'] = True
        def bool_as_schema(s): s['$defs']['CanonicalCodewordRecord']['properties']['membership'] = False
        def loosen_signature(s): s['$defs']['StateSignature'].pop('pattern')
        def force_ninth(s): s['$defs']['StateBits']['prefixItems'] = [{}]*8 + [{'const': 0}]
        mutations = [('missing-minItems', remove_min), ('missing-maxItems', remove_max),
                     ('nonbinary-allowed', broaden_bits), ('membership-not-checked', remove_membership),
                     ('wrong-space-allowed', remove_space), ('missing-bits-allowed', remove_required),
                     ('unknown-fields-allowed', allow_extra), ('boolean-metadata-lift', bool_as_schema),
                     ('signature-alphabet-unchecked', loosen_signature), ('ninth-state-bit-forced-zero', force_ninth)]
        rows = []
        for name, change in mutations:
            bad = deepcopy(self.schema)
            change(bad)
            Draft202012Validator.check_schema(bad)
            witnesses = []
            for case in self.cases:
                if self.validator(case['schema_ref'], bad).is_valid(self.fixtures[case['id']]) != case['expected_valid']:
                    witnesses.append(case['id'])
            require(bool(witnesses), f'Mutation escaped: {name}')
            rows.append({'mutation': name, 'detected_by': witnesses})
        return {'introduced_faults': len(rows), 'detected_faults': len(rows), 'outcomes': rows}

    def offline(self) -> dict[str, Any]:
        require(not self.network_requests, 'Normal validation attempted retrieval.')
        validator = ExactJsonValidator({'$ref': 'https://example.invalid/unapproved.schema.json'}, registry=self.registry)
        failed = False
        try:
            validator.is_valid({})
        except Exception:
            failed = True
        require(failed and self.network_requests == ['https://example.invalid/unapproved.schema.json'],
                'Unknown reference did not fail closed.')
        return {'normal_validation_external_retrievals': 0,
                'deliberately_unresolved_reference': 'blocked locally before network access'}

    def run(self) -> dict[str, Any]:
        for name, test in [('schema_and_fixture_catalog', self.meta_and_catalog),
                           ('bound_fixtures_and_reasons', self.fixture_checks),
                           ('pinned_canonical_set', self.canonical_set),
                           ('exhaustive_values_and_round_trips', self.exhaustive_values),
                           ('exhaustive_transformations', self.transformations),
                           ('raw_json_and_numeric_precision', self.raw_json),
                           ('ownership_and_order', self.ownership_and_order),
                           ('root_dispatch', self.root_dispatch),
                           ('mutation_detection', self.mutations),
                           ('offline_reference_policy', self.offline)]:
            self.group(name, test)
        outcomes = {'candidate': 'YWE-ASH-VALUES-20260918-1',
                    'status': 'pass' if all(r['status'] == 'pass' for r in self.results) else 'fail',
                    'groups': self.results}
        digest = sha256(json.dumps(outcomes, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
        files = {}
        for folder in ('schemas', 'fixtures', 'verification'):
            for path in sorted((self.root / folder).glob('*')):
                if path.is_file():
                    files[path.relative_to(self.root).as_posix()] = sha256(path.read_bytes()).hexdigest()
        return {'observed_at': datetime.now(timezone.utc).isoformat(),
                'environment': {'python': platform.python_version(), 'platform': platform.platform(),
                                'jsonschema': version('jsonschema'), 'referencing': version('referencing'),
                                'number_adapter': 'ExactJsonValidator accepts exact integral Decimal values per JSON Schema integer semantics'},
                'source_commit': self.code_source['commit'], 'input_sha256': files,
                'result_sha256': digest, 'results': outcomes,
                'limits': ['External review prototype only; not integrated product behavior.',
                           'No full repository suite, independent reviewer acceptance, or realization preflight.',
                           'No recovery, admissibility, game, platform, or release acceptance.']}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('Report exists; choose a new report path to preserve evidence.')
    report = ContractVerification(args.root.resolve()).run()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=True)
        f.write('\n')
    for group in report['results']['groups']:
        print(group['status'].upper(), group['group'], group.get('message', ''))
    print('RESULT', report['results']['status'], report['result_sha256'])
    return 0 if report['results']['status'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())

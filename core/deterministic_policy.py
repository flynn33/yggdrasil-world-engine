"""Exact integer deterministic Core policies (YWE-REQ-0051)."""
from __future__ import annotations
import hashlib
import json
from . import core_values as cv


def _round_even(numerator, denominator=cv.Q6):
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    if remainder * 2 > denominator or (remainder * 2 == denominator and quotient % 2):
        quotient += 1
    return sign * quotient


def _selection_draw(request, counter):
    body = {'algorithm': 'YWE.CORE.SELECT.V1', 'domain': request.domain,
            'binding_hash': request.binding_sha256, 'context_hash': request.context_sha256,
            'seed_token': request.seed_token, 'counter': counter}
    wire = json.dumps(body, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode('ascii')
    return int.from_bytes(hashlib.sha256(wire).digest()[:8], 'big')


class DeterministicPolicy(cv._ConfiguredOwner):
    __slots__ = ()
    CORE_OWNER = 'DETERMINISTIC_POLICY'

    def __init__(self, binding):
        cv._initialize_owner(self, binding, DeterministicPolicy)

    def configuration(self):
        return cv._owner_configuration(self, DeterministicPolicy)

    def validate_owned_result(self, result):
        try:
            return cv._validate_result(self, result, DeterministicPolicy.configuration(self))
        except cv.CoreContractError:
            return False

    def normalize(self, options):
        DeterministicPolicy.configuration(self)
        if type(options) is not tuple or len(options) > 64:
            cv._fail('options')
        for option in options:
            if type(option) is not cv.WeightedOption:
                cv._fail('options')
            cv.revalidate_value(option)
        ordered = tuple(sorted(options, key=lambda row: row.option_id))
        if len({row.option_id for row in ordered}) != len(ordered):
            cv._fail('options')
        total = sum(row.weight for row in ordered)
        reference = 'normalize:' + hashlib.sha256(json.dumps(
            [[row.option_id, row.weight] for row in ordered], separators=(',', ':'), ensure_ascii=True
        ).encode('ascii')).hexdigest()
        if not total:
            value = cv.WeightedAllocation(tuple(cv.WeightedOption(row.option_id, 0) for row in ordered), 0)
            return cv._operation_result(self, DeterministicPolicy, reference, value, 'NORMALIZATION',
                                        status='NO_OP', code='CORE_NO_POSITIVE_WEIGHT', field='options',
                                        explanation='All explicit option weights are zero; no distribution was invented.')
        floors = [row.weight * cv.Q6 // total for row in ordered]
        rank = sorted(range(len(ordered)), key=lambda i: (-(ordered[i].weight * cv.Q6 % total), ordered[i].option_id))
        for index in rank[:cv.Q6 - sum(floors)]:
            floors[index] += 1
        value = cv.WeightedAllocation(tuple(cv.WeightedOption(row.option_id, weight)
                                             for row, weight in zip(ordered, floors)), cv.Q6)
        return cv._operation_result(self, DeterministicPolicy, reference, value, 'NORMALIZATION',
                                    explanation='Hamilton allocation retained every explicit option and exact total.')

    def select(self, request):
        binding = DeterministicPolicy.configuration(self)
        if type(request) is not cv.SelectionRequest:
            cv._fail('request')
        cv.revalidate_value(request)
        reference = 'select:' + cv._wire_digest(request)
        if request.binding_sha256 != cv._wire_digest(binding):
            return cv._operation_result(self, DeterministicPolicy, reference, None, 'BINDING',
                                        status='REFUSED', code='CORE_BINDING_MISMATCH', field='binding_sha256')
        ordered = tuple(sorted(request.options, key=lambda row: row.option_id))
        total = sum(row.weight for row in ordered)
        if total > 64_000_000:
            return cv._operation_result(self, DeterministicPolicy, reference, None, 'RESOURCE_LIMIT',
                                        status='REFUSED', code='CORE_RESOURCE_LIMIT', field='options')
        if total == 0:
            value = cv.SelectionResult(request, None, 0, None)
            return cv._operation_result(self, DeterministicPolicy, reference, value, 'SELECTION',
                                        status='NO_OP', code='CORE_NO_POSITIVE_WEIGHT', field='options')
        upper = ((1 << 64) // total) * total
        for counter in range(16):
            draw = _selection_draw(request, counter)
            if draw >= upper:
                continue
            remainder = draw % total
            selected = None
            cumulative = 0
            for row in ordered:
                cumulative += row.weight
                if remainder < cumulative:
                    selected = row.option_id
                    break
            value = cv.SelectionResult(request, selected, counter + 1, draw)
            return cv._operation_result(self, DeterministicPolicy, reference, value, 'SELECTION',
                                        explanation='Explicit source-bound SHA256 rejection draw selected an option.')
        value = cv.SelectionResult(request, None, 16, None)
        return cv._operation_result(self, DeterministicPolicy, reference, value, 'SELECTION',
                                    status='PENDING', code='CORE_SELECTION_EXHAUSTED', field='counters_used')

    def measure_existence(self, inputs):
        DeterministicPolicy.configuration(self)
        if type(inputs) is not cv.ExistentialMetricInputs:
            cv._fail('inputs')
        cv.revalidate_value(inputs)
        numerator = (inputs.coefficient_c * inputs.compressibility_q6
                     + inputs.coefficient_s * inputs.symmetry_q6
                     + inputs.coefficient_p * inputs.persistence_q6
                     - inputs.coefficient_h * inputs.entropy_q6)
        value = cv.ExistenceMeasure(inputs, _round_even(numerator))
        reference = 'existence:' + cv._wire_digest(inputs)
        return cv._operation_result(self, DeterministicPolicy, reference, value, 'EXISTENCE',
                                    evidence=inputs.evidence_refs,
                                    explanation='Explicit declared measurements were evaluated with one ties-to-even division.')

    def merge_bias(self, before, terms, *, logical_epoch, retention_q6):
        DeterministicPolicy.configuration(self)
        if type(before) is not cv.BiasState or type(terms) is not tuple or len(terms) > 512:
            cv._fail('terms')
        cv.revalidate_value(before)
        for event in terms:
            if type(event) is not cv.BiasEvent:
                cv._fail('terms')
            cv.revalidate_value(event)
        if type(logical_epoch) is not int or not 0 <= logical_epoch < 1 << 64:
            cv._fail('logical_epoch')
        if type(retention_q6) is not int or not 0 <= retention_q6 <= cv.Q6:
            cv._fail('retention_q6')
        shape = [cv._wire_digest(before), [cv._wire_digest(event) for event in terms], logical_epoch, retention_q6]
        reference = 'bias:' + hashlib.sha256(json.dumps(shape, separators=(',', ':')).encode('ascii')).hexdigest()

        def refuse(code, field):
            return cv._operation_result(self, DeterministicPolicy, reference, before, 'BIAS_MERGE',
                                        status='REFUSED', code=code, field=field,
                                        evidence=(before.state_ref,))

        keys = tuple(sorted({(term.domain, term.target_id) for event in before.events for term in event.terms}))
        ranks = tuple('bias:' + format(index, '02d') for index in range(len(keys)))
        if tuple(option.option_id for option in before.weights) != ranks:
            return refuse('CORE_PROVENANCE_MISSING', 'weights')
        if logical_epoch < before.logical_epoch:
            return refuse('CORE_EPOCH_REVERSED', 'logical_epoch')
        steps = logical_epoch - before.logical_epoch
        if steps > 1024:
            return refuse('CORE_RESOURCE_LIMIT', 'logical_epoch')
        events = {}
        for event in before.events:
            prior = events.get(event.event_id)
            if prior is not None and cv._wire_digest(prior) != cv._wire_digest(event):
                return refuse('CORE_FACT_CONFLICT', 'event_id')
            events[event.event_id] = event
        new_events = []
        for event in terms:
            prior = events.get(event.event_id)
            if prior is not None:
                if cv._wire_digest(prior) != cv._wire_digest(event):
                    return refuse('CORE_FACT_CONFLICT', 'event_id')
                continue
            events[event.event_id] = event
            new_events.append(event)
        all_keys = tuple(sorted({(term.domain, term.target_id) for event in events.values() for term in event.terms}))
        if len(all_keys) > 64 or len(events) > 512:
            return refuse('CORE_RESOURCE_LIMIT', 'events')
        current = dict(zip(keys, (option.weight for option in before.weights)))
        for key in keys:
            weight = current[key]
            for unused in range(steps):
                weight = weight * retention_q6 // cv.Q6
            current[key] = weight
        for event in new_events:
            for term in event.terms:
                key = term.domain, term.target_id
                current[key] = current.get(key, 0) + term.contribution_q6
        weights = tuple(cv.WeightedOption('bias:' + format(index, '02d'), min(cv.Q6, max(0, current.get(key, 0))))
                        for index, key in enumerate(all_keys))
        proposed = cv.BiasState(reference + ':state', logical_epoch,
                                tuple(events[key] for key in sorted(events)), weights)
        value = cv.BiasUpdateResult(before, proposed, 'PROPOSED_ONLY')
        return cv._operation_result(self, DeterministicPolicy, reference, value, 'BIAS_MERGE',
                                    effect='PROPOSED_ONLY', evidence=(before.state_ref,),
                                    explanation='Current weights were decayed and only new event contributions were summed before one clamp.')

"""Pure bounded final-frontier topology owner [YWE-REQ-0047]."""
from itertools import product

from . import generation_values as values
from . import state_values as state


class ReferenceTopologyGenerator:
    __slots__ = ("_model", "_policy", "_cookie", "_self_identity")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("ReferenceTopologyGenerator is final")

    def __init__(self, state_model, policy_binding):
        configuration = values._model_configuration(state_model, policy_binding)
        if configuration[0].canonical_binding.aggregate_sha256 not in values.CURRENT_PRODUCER_AGGREGATES:
            values._fail("model.canonical_binding", "GENERATION_SOURCE_UNSUPPORTED")
        self._model, self._policy = state_model, policy_binding
        self._cookie = values._issue_producer_cookie(self, state_model, policy_binding)
        self._self_identity = self

    def configuration(self):
        return values._owned_configuration(self, ReferenceTopologyGenerator)

    def validate_owned_result(self, result):
        if type(self) is not ReferenceTopologyGenerator:
            return False
        try:
            configuration = ReferenceTopologyGenerator.configuration(self)
            return values._validate_seal(result, self, self._cookie,
                                         (values.TopologyResult, values.TopologyFailure), configuration)
        except (values.GenerationContractError, state.StateContractError, AttributeError):
            return False

    def generate(self, request):
        configuration = ReferenceTopologyGenerator.configuration(self)
        values._exact(request, values.TopologyRequest, "request")
        values.revalidate_value(request)
        validation = values._validate_origin(self._model, request, configuration)
        failure = values.admission_failure(request, configuration[0], validation)
        if failure is not None:
            return values._seal(values._failure(request, configuration, validation, *failure), self, self._cookie)
        nodes = []
        visited = 0
        for depth in range(request.depth + 1):
            for digits in product("012", repeat=depth):
                visited += 1
                path = "r" + "".join(digits)
                node = values.TopologyNode(
                    f"topology:{request.seed_token}:{path}",
                    None if depth == 0 else f"topology:{request.seed_token}:{path[:-1]}",
                    depth, int(path[1:], 3) if depth else 0,
                    "root" if depth == 0 else ("continuation", "positive", "negative")[int(path[-1])], path)
                if depth == request.depth:
                    nodes.append(node)
        topology_reference = request.request_reference + ":topology"
        payload = values.TopologyDiagnostic(request.request_reference, topology_reference,
                                             request.origin_diagnosis.parsed_state, request.seed_token,
                                             request.depth, len(nodes), visited, "COMPLETE", None,
                                             values.topology_notes(request.depth, len(nodes), visited))
        origin = request.origin_diagnosis.emitted_diagnostics[0]
        envelope = state.DiagnosticEnvelope("TOPOLOGY", origin.envelope.severity, "PROCESSING", "RESOLVED",
                                             origin.envelope.subject_reference, origin.diagnostic_reference,
                                             origin.diagnostic_reference, values.TOPOLOGY_RULES,
                                             "Topology expansion completed.", payload.notes)
        record = values.GenerationDiagnosticRecord(request.request_reference + ":diagnostic:topology", envelope, payload)
        result = values.TopologyResult(topology_reference, request, self._policy, configuration[0], validation,
                                        request.origin_diagnosis.parsed_state, tuple(nodes), visited, (record,))
        return values._seal(result, self, self._cookie)

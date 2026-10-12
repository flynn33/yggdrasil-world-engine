"""Pure declared five-axiom owner [YWE-REQ-0047]."""
from . import generation_values as values
from . import state_values as state


class ReferenceAxiomEvaluator:
    __slots__ = ("_model", "_policy", "_cookie", "_self_identity")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("ReferenceAxiomEvaluator is final")

    def __init__(self, state_model, policy_binding):
        configuration = values._model_configuration(state_model, policy_binding)
        if configuration[0].canonical_binding.aggregate_sha256 not in values.CURRENT_PRODUCER_AGGREGATES:
            values._fail("model.canonical_binding", "GENERATION_SOURCE_UNSUPPORTED")
        self._model, self._policy = state_model, policy_binding
        self._cookie = values._issue_producer_cookie(self, state_model, policy_binding)
        self._self_identity = self

    def configuration(self):
        return values._owned_configuration(self, ReferenceAxiomEvaluator)

    def validate_owned_result(self, result):
        if type(self) is not ReferenceAxiomEvaluator:
            return False
        try:
            configuration = ReferenceAxiomEvaluator.configuration(self)
            return values._validate_seal(result, self, self._cookie,
                                         (values.AxiomEvaluationResult, values.AxiomEvaluationFailure), configuration)
        except (values.GenerationContractError, state.StateContractError, AttributeError):
            return False

    def evaluate(self, request):
        configuration = ReferenceAxiomEvaluator.configuration(self)
        values._exact(request, values.AxiomRequest, "request")
        values.revalidate_value(request)
        validation = values._validate_origin(self._model, request, configuration)
        failure = values.admission_failure(request, configuration[0], validation)
        if failure is not None:
            return values._seal(values._failure(request, configuration, validation, *failure), self, self._cookie)
        subject = request.subject
        passes = values.axiom_passes(subject)
        overall = all(passes)
        origin = request.origin_diagnosis.emitted_diagnostics[0]
        previous = origin.diagnostic_reference
        severity = origin.envelope.severity
        records = []
        for index, passed in enumerate(passes):
            axiom = f"A{index+1}"
            explanation = values.axiom_explanation(axiom, subject)
            impact = "INFO" if passed else "WARNING"
            severity = max((severity, impact), key=values.SEVERITIES.index)
            payload = values.AxiomCheckDiagnostic(axiom, subject, passed, impact,
                                                  values.OPERATORS[index], values.OPERANDS[index],
                                                  overall if index == 4 else None, explanation)
            word = "passed" if passed else "failed"
            summary = (f"{axiom} axiom check {word}." if index < 4 else
                       f"A5 component {word}; overall {'passed' if overall else 'failed'}.")
            reference = request.request_reference + f":diagnostic:A{index+1}"
            disposition_pass = overall if index == 4 else passed
            envelope = state.DiagnosticEnvelope("AXIOM", severity, "PROCESSING",
                                                 "RESOLVED" if disposition_pass else "BLOCKED",
                                                 origin.envelope.subject_reference, previous,
                                                 origin.diagnostic_reference, values.AXIOM_RULES[index], summary,
                                                 (explanation, "Measurements and subject provenance are declared reference input."))
            records.append(values.GenerationDiagnosticRecord(reference, envelope, payload))
            previous = reference
        diagnostic = values.AxiomDiagnostic(*passes, overall, tuple(record.payload.explanation for record in records))
        result = values.AxiomEvaluationResult(request.request_reference + ":axioms", request, self._policy,
                                               configuration[0], validation, diagnostic, tuple(records))
        return values._seal(result, self, self._cookie)

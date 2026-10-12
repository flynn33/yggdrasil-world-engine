"""Bounded interpretation pressure over explicit profile and truth inputs."""
import hashlib
import itertools
import json
import re
from dataclasses import dataclass
from .. import core_values as cv
from ..deterministic_policy import _round_even
from ..perception_engine.perception import _truth_facts, _contradictions


def _pair_id(first, second):
    raw = json.dumps(sorted((first,second)),ensure_ascii=True,separators=(',',':')).encode('ascii')
    return 'pair:' + hashlib.sha256(raw).hexdigest()


def _relation(first, second):
    for field, relation, delta in (('contradicts','CONTRADICTION',-1000000),
                                   ('friction_with','FRICTION',-350000),
                                   ('compatible_with','COMPATIBILITY',100000)):
        if second.archetype_id in getattr(first,field) or first.archetype_id in getattr(second,field):
            return relation,delta
    return 'NEUTRAL',0


@dataclass(frozen=True,slots=True)
class _EvaluationCookie:
    issuer: object
    original: object
    wire_sha256: str
    provenance: object
    pressure_tags: tuple


class NarrativeEngine(cv._ConfiguredOwner):
    __slots__ = ()
    CORE_OWNER = 'NARRATIVE'

    def __init__(self, binding):
        cv._initialize_owner(self,binding,NarrativeEngine)

    def configuration(self):
        return cv._owner_configuration(self,NarrativeEngine)

    def validate_owned_result(self,result):
        try:
            return cv._validate_result(self,result,NarrativeEngine.configuration(self))
        except cv.CoreContractError:
            return False

    @staticmethod
    def _compile_registry(primary_sources,matrix_source,*,registry_id,evidence_ref):
        """Compile original lexemes; the caller supplies bytes, never file IO."""
        import yaml
        from decimal import Decimal
        cv._text(registry_id,'ID','registry_id')
        cv._text(evidence_ref,'REF','evidence_ref')
        if type(primary_sources) is not tuple or not 1<=len(primary_sources)<=7 or type(matrix_source) is not tuple or len(matrix_source)!=2:
            cv._fail('primary_source')
        def load(source):
            if type(source) is not tuple or len(source)!=2:
                cv._fail('primary_source')
            name,raw=source
            cv._text(name,'REF','source_ref')
            if type(raw) is not bytes or len(raw)>cv.MAX_RAW_CORE_BYTES:
                cv._fail('primary_source','CORE_RESOURCE_LIMIT')
            try:
                result=yaml.load(raw.decode('utf-8'),Loader=yaml.BaseLoader)
            except (UnicodeError,yaml.YAMLError):
                cv._fail('primary_source','CORE_PROFILE_CONFLICT')
            def basic(value,active):
                if type(value) is str:
                    return
                if type(value) is not list and type(value) is not dict:
                    cv._fail('primary_source','CORE_PROFILE_CONFLICT')
                if id(value) in active or len(active)>32 or len(value)>4096:
                    cv._fail('primary_source','CORE_PROFILE_CONFLICT')
                active.add(id(value))
                for child in value.values() if type(value) is dict else value:
                    basic(child,active)
                active.remove(id(value))
            basic(result,set())
            if type(result) is not dict:
                cv._fail('primary_source','CORE_PROFILE_CONFLICT')
            return name,hashlib.sha256(raw).hexdigest(),result
        def seq(row,name):
            value=row.get(name,[])
            if type(value) is not list or any(type(item) is not str for item in value):
                cv._fail('archetypes','CORE_PROFILE_CONFLICT')
            return tuple(value)
        def q6(value):
            if type(value) is not str or re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?',value) is None:
                cv._fail('wolf_bias','CORE_PROFILE_CONFLICT')
            result=int(Decimal(value)*cv.Q6)
            if not -cv.Q6<=result<=cv.Q6:
                cv._fail('wolf_bias','CORE_PROFILE_CONFLICT')
            return result
        compiled,clusters,sources=[],[],[]
        for source in primary_sources:
            name,digest,document=load(source)
            sources.append((name,digest))
            if type(document.get('records')) is not list:
                cv._fail('archetypes','CORE_PROFILE_CONFLICT')
            for row in document['records']:
                if type(row) is not dict:
                    cv._fail('archetypes','CORE_PROFILE_CONFLICT')
                identifier=row.get('id')
                family=row.get('family',document.get('family'))
                wolf=row.get('wolf_bias')
                if wolf is not None:
                    if type(wolf) is not dict or set(wolf)!= {'white','dark'}:
                        cv._fail('wolf_bias','CORE_PROFILE_CONFLICT')
                    wolf=cv.WolfBias(q6(wolf['white']),q6(wolf['dark']))
                affinities=row.get('downstream_affinities',{})
                if type(affinities) is not dict:
                    cv._fail('downstream_affinities','CORE_PROFILE_CONFLICT')
                typed_affinities=tuple(cv.ArchetypeAffinity(domain,tuple(values)) for domain,values in sorted(affinities.items())
                    if type(values) is list and all(type(item) is str for item in values))
                if len(typed_affinities)!=len(affinities):
                    cv._fail('downstream_affinities','CORE_PROFILE_CONFLICT')
                compiled.append(cv.ArchetypeRecord(identifier,family,seq(row,'symbolic_function'),seq(row,'truth_modes'),seq(row,'shadow_modes'),
                    seq(row,'realm_bias'),wolf,seq(row,'player_phase_bias'),seq(row,'compatible_with'),seq(row,'friction_with'),seq(row,'contradicts'),
                    typed_affinities,seq(row,'manifestation_hints'),(name,evidence_ref)))
                if family=='cluster':
                    risk=row.get('contradiction_risk')
                    if type(risk) is not str or not risk:
                        cv._fail('contradiction_risk_ref','CORE_PROFILE_CONFLICT')
                    clusters.append(cv.ClusterRecord(identifier,seq(row,'members'),seq(row,'lawful_basis'),
                        row.get('stability_mode','').upper(),'risk:'+hashlib.sha256(risk.encode('utf-8')).hexdigest()))
        matrix_name,matrix_digest,matrix=load(matrix_source)
        index=matrix.get('relationship_index')
        if type(index) is not dict:
            cv._fail('relationship_source','CORE_PROFILE_CONFLICT')
        for row in compiled:
            actual=index.get(row.archetype_id)
            if type(actual) is not dict:
                cv._fail('relationship_source','CORE_PROFILE_CONFLICT')
            for key,field in (('compatible','compatible_with'),('friction','friction_with'),('contradiction','contradicts')):
                if tuple(sorted(seq(actual,key)))!=tuple(sorted(getattr(row,field))):
                    cv._fail('relationship_source','CORE_PROFILE_CONFLICT')
        raw_hash=hashlib.sha256(json.dumps(sorted(sources),ensure_ascii=True,separators=(',',':')).encode('ascii')).hexdigest()
        return cv.ArchetypeRegistry(registry_id,cv.RegistrySource(registry_id+':primary',raw_hash,evidence_ref),
            cv.RegistrySource(matrix_name,matrix_digest,evidence_ref),tuple(sorted(compiled,key=lambda row:row.archetype_id)),tuple(sorted(clusters,key=lambda row:row.cluster_id)))

    def evaluate_archetypes(self,snapshot,context,registry):
        binding = NarrativeEngine.configuration(self)
        if type(snapshot) is not cv.CosmicPatternSnapshot or type(context) is not cv.ArchetypeContext or type(registry) is not cv.ArchetypeRegistry:
            cv._fail('inputs')
        for value in (snapshot,context,registry):
            cv.revalidate_value(value)
        reference = 'archetypes:' + hashlib.sha256((''.join(cv._wire_digest(value) for value in (snapshot,context,registry))).encode('ascii')).hexdigest()
        def refuse(code,field):
            return cv._operation_result(self,NarrativeEngine,reference,None,'ARCHETYPE_SCORE',status='REFUSED',code=code,field=field,
                evidence=(snapshot.snapshot_ref,context.context_ref,registry.registry_id))
        if cv._wire_digest(snapshot.binding) != cv._wire_digest(binding):
            return refuse('CORE_BINDING_MISMATCH','binding')
        if sum(row.weight for row in context.realm_pressure)>cv.Q6 or len({row.option_id for row in context.realm_pressure}) != len(context.realm_pressure):
            return refuse('CORE_VALUE_INVALID','realm_pressure')
        records = tuple(sorted(registry.archetypes,key=lambda row:row.archetype_id))
        ids = {row.archetype_id for row in records}
        if any(link not in ids for row in records for field in ('compatible_with','friction_with','contradicts') for link in getattr(row,field)):
            return refuse('CORE_UNKNOWN_REFERENCE','relationships')
        if any(member not in ids for cluster in registry.clusters for member in cluster.member_ids):
            return refuse('CORE_UNKNOWN_REFERENCE','member_ids')
        if len(records)*(len(records)-1)//2>256:
            return refuse('CORE_RESOURCE_LIMIT','relationships')
        scores,reasons = {},{}
        for row in records:
            value = 0
            reason = []
            for field,coefficient in (('symbolic_tags',1000000),('truth_tags',800000),('shadow_tags',600000)):
                if set(getattr(row,field)) & set(getattr(context,field)):
                    value += coefficient
                    reason.append(field)
            features = [('realm_bias',350000,sum(option.weight for option in context.realm_pressure if option.option_id in row.realm_bias))]
            wolf = 0
            if row.wolf_bias is not None and context.wolf_pressure is not None:
                wolf = _round_even(row.wolf_bias.white_q6*context.wolf_pressure.white_q6 + row.wolf_bias.dark_q6*context.wolf_pressure.dark_q6)
            features.extend((('wolf_bias',200000,wolf),('player_phase_bias',250000,cv.Q6 if context.player_phase is not None and context.player_phase in row.player_phase_bias else 0)))
            for field,coefficient in (('recurrence_refs',150000),('myth_refs',100000),('prophecy_refs',100000)):
                features.append((field,coefficient,cv.Q6 if set(getattr(context,field)) & set(row.evidence_refs) else 0))
            for field,coefficient,magnitude in features:
                increment = _round_even(coefficient*magnitude)
                value += increment
                if magnitude:
                    reason.append(field)
            if context.requested_domain is not None and context.requested_domain not in tuple(affinity.domain for affinity in row.downstream_affinities):
                value -= 200000
                reason.append('SHALLOW_AFFINITY')
            scores[row.archetype_id],reasons[row.archetype_id] = value,reason
        relations = []
        for first,second in itertools.combinations(records,2):
            relation,delta = _relation(first,second)
            allowed = relation != 'CONTRADICTION' and relation != 'FRICTION'
            if relation == 'CONTRADICTION':
                allowed = _pair_id(first.archetype_id,second.archetype_id) in context.higher_order_pairs
            if relation == 'FRICTION':
                allowed = _pair_id(first.archetype_id,second.archetype_id) in context.allowed_tension_pairs
            scores[first.archetype_id]+=delta
            scores[second.archetype_id]+=delta
            relations.append((first.archetype_id,second.archetype_id,relation,delta,allowed))
        rank = {identifier:index for index,identifier in enumerate(sorted(ids,key=lambda identifier:(-scores[identifier],identifier)))}
        suppressed = {}
        observations = []
        for first,second,relation,delta,allowed in relations:
            loser = None
            if not allowed:
                winner,loser = (first,second) if rank[first]<rank[second] else (second,first)
                suppressed.setdefault(loser,winner)
            observations.append(cv.RelationObservation(first,second,relation,delta,allowed,loser))
        dominant = tuple(sorted(identifier for identifier in ids if identifier not in suppressed and scores[identifier]>=1200000))
        secondary = tuple(sorted(identifier for identifier in ids if identifier not in suppressed and 800000<=scores[identifier]<1200000))
        score_rows = tuple(cv.ArchetypeScore(identifier,scores[identifier],'SUPPRESSED' if identifier in suppressed else 'DOMINANT' if identifier in dominant else 'SECONDARY' if identifier in secondary else 'INELIGIBLE',
            suppressed.get(identifier),tuple(reasons[identifier])) for identifier in sorted(ids))
        clusters = []
        for cluster in sorted(registry.clusters,key=lambda row:row.cluster_id):
            members = tuple(sorted(member for member in cluster.member_ids if member not in suppressed and scores[member]>800000))
            base = sum(scores[member] for member in members)
            bonus = {'STABLE':200000,'CYCLICAL':150000,'THRESHOLD_BASED':250000,'UNSTABLE':-100000}[cluster.stability]
            supported = set(cluster.lawful_basis_refs)<=set(context.satisfied_basis_refs) and cluster.contradiction_risk_ref in context.accepted_risk_refs
            penalty = 0 if supported else -500000
            final = base+bonus+penalty
            active = len(members)>=2 and supported and final>=2100000
            cluster_reasons = tuple(code for condition,code in ((len(members)<2,'INSUFFICIENT_MEMBERS'),(not supported,'UNSUPPORTED_BASIS_OR_RISK'),(final<2100000,'BELOW_THRESHOLD')) if condition)
            clusters.append(cv.ClusterScore(cluster.cluster_id,members,base,bonus,penalty,final,active,cluster_reasons))
        evaluation = cv.ArchetypeEvaluation(reference+':evaluation',snapshot.snapshot_ref,cv._wire_digest(snapshot),context.context_ref,cv._wire_digest(context),registry.registry_id,cv._wire_digest(registry),
            score_rows,tuple(observations),tuple(clusters),dominant,secondary,tuple(row.cluster_id for row in clusters if row.activated))
        pressure = set()
        for row in records:
            if row.archetype_id in dominant or row.archetype_id in secondary:
                for field in ('symbolic_tags','truth_tags','shadow_tags'):
                    pressure.update(set(getattr(row,field)) & set(getattr(context,field)))
        object.__setattr__(evaluation,'_core_result_cookie',_EvaluationCookie(self,evaluation,
            cv._wire_digest(evaluation),snapshot.provenance,tuple(sorted(pressure))))
        return cv._operation_result(self,NarrativeEngine,reference,evaluation,'ARCHETYPE_SCORE',
            status='COMPLETED' if dominant or secondary else 'NO_OP',evidence=(snapshot.snapshot_ref,context.context_ref,registry.registry_id),
            explanation='Every declared score, relation and cluster decision was retained; no world content was created.')

    def read_memory_view(self,truth_input):
        NarrativeEngine.configuration(self)
        return _truth_facts(truth_input)

    def interpret(self,evaluation,truth_input,*,interpretation_ref):
        NarrativeEngine.configuration(self)
        cv._text(interpretation_ref,'ID','interpretation_ref')
        if type(evaluation) is not cv.ArchetypeEvaluation:
            cv._fail('evaluation_ref')
        cv.revalidate_value(evaluation)
        try:
            cookie = object.__getattribute__(evaluation,'_core_result_cookie')
        except AttributeError:
            cookie = None
        if (type(cookie) is not _EvaluationCookie or cookie.issuer is not self or cookie.original is not evaluation or
                type(cookie.wire_sha256) is not str or type(cookie.provenance) is not cv.CoreProvenance or
                type(cookie.pressure_tags) is not tuple or any(type(tag) is not str for tag in cookie.pressure_tags) or
                cookie.wire_sha256 != cv._wire_digest(evaluation)):
            return cv._operation_result(self,NarrativeEngine,interpretation_ref,evaluation,'PROVENANCE',status='REFUSED',code='CORE_PROVENANCE_MISSING',field='evaluation_ref')
        try:
            facts = _truth_facts(truth_input)
        except cv.CoreContractError as error:
            return cv._operation_result(self,NarrativeEngine,interpretation_ref,evaluation,'TRUTH_PRECEDENCE',status='REFUSED',code=error.code,field=error.field_name)
        if len(cookie.pressure_tags)>64:
            return cv._operation_result(self,NarrativeEngine,interpretation_ref,evaluation,'RESOURCE_LIMIT',status='REFUSED',code='CORE_RESOURCE_LIMIT',field='pressure_tags')
        value = cv.NarrativeInterpretation(interpretation_ref,evaluation.evaluation_ref,cv._wire_digest(evaluation),truth_input.scope_ref,
            tuple(sorted({fact.fact_id for fact in facts})),cookie.pressure_tags,_contradictions(facts),cookie.provenance)
        return cv._operation_result(self,NarrativeEngine,interpretation_ref,value,'TRUTH_PRECEDENCE',
            status='COMPLETED' if evaluation.dominant or evaluation.secondary else 'NO_OP',
            evidence=(evaluation.evaluation_ref,truth_input.snapshot_ref),
            explanation='Interpretation retained declared pressures and contradictions without replacing objective truth.')

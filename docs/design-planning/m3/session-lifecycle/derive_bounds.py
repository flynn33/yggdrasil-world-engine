from pathlib import Path
import json, math, hashlib
P=Path(__file__).parent
x=json.loads((P/'SAFE_FIELDS_AND_LIMITS.json').read_text());F=x['fields']
V=json.loads((P/'N3_COMPLETE_SOURCE_VECTORS.bound-input.json').read_text())
D=json.loads((P/'BOUND_INPUT_DOMAINS.json').read_text());E=dict(D['enums'])
I=json.loads((P/x['business_inventory_file']).read_text())
E.update(I['domains'])
E['SessionFieldPath']=I['domains']['SessionFieldPath']
E['SessionFailureCode']=I['domains']['SessionFailureCode']
E['ContainmentTrigger']=E['CanonicalContainmentTrigger']
E['SafeHaltTrigger']=E['CanonicalSafeHaltTrigger']
E['CanonicalRule17']=tuple(dict.fromkeys((*E['CanonicalRule'],*(r for m in V['trigger_rule_mapping'].values() for r in m.values()))))
E['SupportingKindWithoutHistoryPage']=tuple(E['SupportingKind'])+tuple(k for k in x['support_kind_maxima'] if k!='SESSION_HISTORY_PAGE')
for n in ('SourcePin','SafeProfileEvidence','SafeSourceEvidence','SafePredicate','SafeStateValidity','SafeInputState','SafeOrbit','SafeAssessmentEvidence'):F[n]=D['fields'][n]
F['SafeDiagnosticEnvelope']=dict(D['fields']['SafeDiagnosticEnvelope']);F['SafeDiagnosticEnvelope']['rule_ids']='tuple<CanonicalRule17,1..10>'
def encode(v):return json.dumps(v,ensure_ascii=True,allow_nan=False,sort_keys=True,separators=(',',':')).encode('ascii')
def longest(v):return max(v,key=lambda z:len(encode(z)))
cache={}
def maximum(t):
 if t.startswith('Alias'):return 'ref:999999'
 if t.endswith('|null'):return longest([None,maximum(t[:-5])])
 if t.startswith('tuple<'):
  inner,b=t[6:-1].rsplit(',',1);return [maximum(inner)]*int(b.split('..')[-1])
 if t=='Revision':return 'f'*40
 if t=='Sha256':return 'f'*64
 if t.startswith('const_bool:'):return t[11:]=='true'
 if t.startswith('const:'):return int(t[6:]) if t[6:].isdigit() else t[6:]
 if t=='uint64':return 2**64-1
 if t.startswith('uint') and '[' in t:return int(t.rsplit('..',1)[1][:-1])
 if t=='bool':return False
 if t=='Signature':return '111111111'
 if t=='UtcTimestamp':return '9999-12-31T23:59:59.999999Z'
 if t=='TrustedTemplateText':return longest([v for _,v in D['message_templates']])
 if t.startswith('fixed:'):return t[6:]
 if t=='VerifiedCanonicalVector9':return longest([v['canonical_binding'] for v in V['vectors']])
 if t=='VerifiedSourcePathDigest':return longest([r for v in V['vectors'] for r in v['recovery_contract_pins']])
 if t=='VerifiedSourceVectorHash':return longest(x['approved_source_vector_hashes'].values())
 if t in E:return longest(E[t])
 if t in F:
  if t not in cache:cache[t]={k:maximum(v) for k,v in F[t].items()}
  return cache[t]
 if '|' in t:return longest([maximum(s) for s in t.split('|')])
 if t.startswith('enum:'):return longest(E[t[5:]])
 if t.replace('_','').isalnum() and t==t.upper():return t
 raise ValueError(t)
M={k:maximum(k) for k in F if k.startswith('Safe')};S={k:len(encode(v)) for k,v in M.items()}
K={'SESSION_BINDING':'SafeSessionBindingEvidence','SESSION_SOURCE':'SafeSessionSourceEvidence','SESSION_RECOVERY_CONTEXT':'SafeSessionSubmittedRecoveryContextEvidence','SESSION_SNAPSHOT':'SafeSessionSnapshotEvidence','SESSION_CONTEXT':'SafeSessionContextEvidence','SESSION_PUBLICATION':'SafeSessionPublicationEvidence','LIFECYCLE':'SafeLifecycleEvidence','SESSION_HISTORY':'SafeSessionHistoryEvidence','SESSION_TERMINAL_CLOSURE':'SafeSessionTerminalClosureEvidence','SESSION_HISTORY_PAGE':'SafeSessionHistoryPage','SESSION_DENIED':'SafeSessionDeniedEvidence','SESSION_LINK':'SafeSessionChildLinkEvidence','SESSION_REQUEST':'SafeSessionRequestEvidence','SESSION_AUTHORITY':'SafeSessionAuthorityEvidence','SESSION_BOUNDARY':'SafeSessionBoundaryEvidence','SESSION_CAUSE':'SafeSessionCauseEvidence','SESSION_COMMAND':'SafeSessionCommandEvidence','SESSION_FAILURE':'SafeSessionFailureEvidence','RESOLUTION_TARGET':'SafeResolutionTargetEvidence','SESSION_RESOLUTION':'SafeSessionResolutionEvidence'}
B=x['support_kind_maxima'];A=x['alias_derivation_counts'];pages=[]
for i in range(B['SESSION_HISTORY_PAGE']):
 row=dict(M['SafeSessionHistoryPage']);row['page_index']=i
 row['record_references']=[M['SafeHistoryRecordReference']]*max(0,min(64,1024-64*i))
 row['supporting_references']=[M['SafeSupportingReference']]*max(0,min(64,x['page_assembly']['supporting_limit_without_pages']-64*i));pages.append(row)
node_bytes={k:n*S[K[k]] for k,n in B.items() if k!='SESSION_HISTORY_PAGE'}
page_bytes=sum(len(encode(r)) for r in pages);new_support=sum(node_bytes.values())+page_bytes
old_extra=16*S['SafeProfileEvidence']+16*S['SafeSourceEvidence']+40*S['SafeAssessmentEvidence']+36*S['SafeZeroStepRecoveryDiagnostic']
# Typed resolution's pure target lives inside RESOLUTION_TARGET, not ASSESSMENT; no fake record.
reservation_total=new_support+old_extra+4*32768+3*32768
terms={'new_node_aliases':sum(B.values()),'submitted_binding_session_references':A['bindings'],'snapshot_nullable_containment_halt_active_refs':A['snapshots']*3,'request_command_session_authority_refs':A['requests']*3,'authority_boundary_source_triples_plus_observation':(A['authorities']+A['boundaries'])*6,'cause_external_five_refs':A['causes']*5,'publication_lease_cause_proof_refs':A['publications']*3,'context_operation_refs':A['contexts'],'per_command_clock_source':A['ordinary_commands'],'lifecycle_subject_parent_root_refs':A['lifecycle']*3,'separate_denial_refs':A['denials']*3,'fresh_assessment_reference_occurrences':A['fresh_assessments']*26,'existing_domain_profile_source_refs':16*6+16*2,'primary_failure_refs':A['ordinary_commands'],'three_finish_response_slots_op_plus_four_refs':3*A['ordinary_commands']*5,'origin_completion_operation_refs':A['ordinary_commands'],'resolution_target_observation_refs':A['resolution_targets']*2,'resolution_control_external_refs':A['resolutions']*10,'fixed_policy_lineage_refs':3,'raw_snapshot_identity_refs':A['snapshots'],'snapshot_current_assessment_refs':A['snapshots'],'lease_active_snapshot_refs':18,'post_assessment_output_refs':18,'post_assessment_completion_operation_refs':18,'denial_finish_response_slots':16*5,'binding_raw_identity_refs':19*2,'context_observation_refs':53,'publication_identity_refs':18,'new_zero_step_bridge_nodes':36,'submitted_recovery_context_external_refs':2*17,'submitted_request_authority_boundary_provenance_refs':18*4,'terminal_closure_external_aliases':6}
alias=sum(terms.values())
# Scope reservation rounds independent alias bound upward to next256, bytes next32768.
fixed_alias=((alias+255)//256)*256
fixed_bytes=((reservation_total+32767)//32768)*32768
fixed_support=((new_support+old_extra+32767)//32768)*32768
assert fixed_alias<=6144 and fixed_support<=2097152 and fixed_bytes<=33554432
x.setdefault('fixed_scope_reservation', {'events':4,'incidents':1}).update({'novel_aliases':fixed_alias,'bytes':fixed_bytes,'supporting_bytes':fixed_support})
(P/'SAFE_FIELDS_AND_LIMITS.json').write_text(json.dumps(x,indent=2)+'\n',newline='\n')
report={'status':'EXECUTED_STRUCTURAL_BOUND_NOT_RUNTIME_ACCEPTANCE','limits':x['enforced_business_limits'],'leaf_encoded_bytes':S,'per_kind_encoded_bytes_upper':node_bytes,'page_count':len(pages),'largest_page_bytes':max(map(lambda r:len(encode(r)),pages)),'page_encoded_bytes_upper':page_bytes,'new_safe_support_nodes':sum(B.values()),'old_domain_support_node_limit':1928,'non_page_pin_inventory_limit':x['page_assembly']['supporting_limit_without_pages'],'new_safe_support_bytes_upper':new_support,'old_domain_additional_allocation_bytes_upper':old_extra,'old_domain_formula':'16*profile+16*source+40*freshAssessment+36*zeroStepBridge (4 child assessment nodes across2RECOVER + up to16post-modeassessment nodes +20conservativeunusedallocations; eachassessment emits2records)','four_event_bytes_upper':4*32768,'incident_health_meta_bytes_upper':3*32768,'scope_encoded_bytes_upper':reservation_total,'lifetime_graph_rounded_envelope':x['fixed_scope_reservation'],'scope_byte_margin':fixed_bytes-reservation_total,'support_byte_margin':fixed_support-new_support-old_extra,'alias_terms':terms,'novel_alias_occurrence_upper':alias,'alias_margin':fixed_alias-alias,'global_caps_unchanged':{'events':1024,'aliases':6144,'total_bytes':33554432,'support_bytes':2097152,'incidents':32,'active_scopes':8,'duration_ms':600000},'offered_event_sum':{'two_N2_episodes':2*768,'fresh_origin_records':8,'lifecycle_and_control_records':36,'required_post_mode_records':32,'terminal_denials':16,'sum':2*768+8+36+32+16,'admitted_retained_record_limit':1024,'meaning':'Offered worst case exceeds actual global capacity. Admission must refuse; do not relabel all offered work as admitted.'},'sequence_constraints':['Complete fresh origin scopes before N2 reserves32incidents.','Finish N2 exactly once through existing Engine, then admit lifecycle scope.','Lifecycle finishing frees outstanding reservations but retained incidents/permanent aliases still count.','No automatic purge/reset/unpin/cap increase.','Resolution pure proof emits0events; required actual post-mode StateModel assessment emits2 within lifecycle shared4slot budget.','Record supports commit before event acknowledgment; one once-final observation cannot include its own returned response.']}
(P/'MAXIMUM_SPECIMENS.json').write_text(json.dumps({'leaves':M,'pages':pages},indent=2)+'\n',newline='\n')
(P/'BOUND_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n')
print(json.dumps({k:report[k] for k in ('new_safe_support_nodes','new_safe_support_bytes_upper','old_domain_additional_allocation_bytes_upper','scope_encoded_bytes_upper','lifetime_graph_rounded_envelope','novel_alias_occurrence_upper','largest_page_bytes','offered_event_sum')},indent=2))

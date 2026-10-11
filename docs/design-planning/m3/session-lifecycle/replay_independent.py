from pathlib import Path
import json, hashlib, subprocess, sys
P=Path(__file__).parent
for n in ('derive_bounds.py','derive_command_reservations.py'):
 subprocess.run([sys.executable,'-B',str(P/n)],check=True,capture_output=True)
# Independent verification uses encoded emitted leaves/pages, not generator's cached size table.
r=json.loads((P/'BOUND_REPORT.json').read_text());x=json.loads((P/'SAFE_FIELDS_AND_LIMITS.json').read_text());m=json.loads((P/'MAXIMUM_SPECIMENS.json').read_text());enc=lambda v:json.dumps(v,allow_nan=False,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode('ascii')
actual={k:len(enc(v)) for k,v in m['leaves'].items()}
assert actual==r['leaf_encoded_bytes']
assert actual['SafeUnavailablePostAssessmentFacts']==290 and actual['SafeSessionFailureEvidence']==1290
assert sum(len(p['record_references']) for p in m['pages'])==1024
assert sum(len(p['supporting_references']) for p in m['pages'])==2504
assert len(m['pages'])==40
assert all(len(p['record_references'])<=64 and len(p['supporting_references'])<=64 for p in m['pages'])
assert max(len(enc(p)) for p in m['pages'])==12877
assert sum(len(enc(p)) for p in m['pages'])==r['page_encoded_bytes_upper']
assert all(len(enc(v))<=32768 for v in m['leaves'].values())
new=sum(r['per_kind_encoded_bytes_upper'].values())+sum(len(enc(p)) for p in m['pages'])
old=16*actual['SafeProfileEvidence']+16*actual['SafeSourceEvidence']+40*actual['SafeAssessmentEvidence']+36*actual['SafeZeroStepRecoveryDiagnostic']
assert new==972678 and old==373204
assert new+old+4*32768+3*32768==1575258
assert r['novel_alias_occurrence_upper']==sum(r['alias_terms'].values())==4748
assert r['per_command_alias_occurrence_upper']==sum(r['per_command_alias_terms'].values())==324
assert r['per_command_encoded_bytes_upper']==324066
assert r['per_terminal_command_encoded_bytes_upper']==645088
assert r['regular_command_reservation']=={'events':4,'incidents':1,'aliases':512,'bytes':327680,'supporting_bytes':98304}
assert r['terminal_command_reservation']=={'events':4,'incidents':1,'aliases':512,'bytes':655360,'supporting_bytes':425984}
g=json.loads((P/'REPRESENTATION_GRAPH_CONTROL.json').read_text())
roots=g['non_page_roots'];pages=g['pages'];flat=[z for pg in pages for z in pg['supporting_references']]
assert len(roots)==len(flat)==2504
assert set((z['kind'],z['evidence_reference']) for z in roots)==set((z['kind'],z['evidence_reference']) for z in flat)
assert len({z['evidence_reference'] for z in roots})==2504
assert len({pg['evidence_reference'] for pg in pages})==40
assert not ({z['evidence_reference'] for z in roots}&{pg['evidence_reference'] for pg in pages})
assert len([z for pg in pages for z in pg['record_references']])==1024
assert all(len(enc(pg))<=r['largest_page_bytes'] for pg in pages)
assert hashlib.sha256((P/x['business_inventory_file']).read_bytes()).hexdigest()==x['business_inventory_sha256']
# Boundary arithmetic controls; no runtime or private collector mutation is performed.
boundary_cases=[]
for label,held,need,cap in [('emptyordinaryevents',0,4,1024),('ordinarylastfit',1020,4,1024),('ordinaryoverflow',1021,4,1024),('2fullN2events',768,768,1024),('N2afterlifealiases',214,5931,6144),('N2exactaliasfit',213,5931,6144),('N2activelifeincident',1,32,32),('afterN2incidentfree',0,1,32),('afterN2retained32incidents',32,1,32),('ordinarysupportfit',2097152-98304,98304,2097152),('ordinarysupportoverflow',2097152-98304+1,98304,2097152),('terminalsupportfit',2097152-425984,425984,2097152),('terminalsupportoverflow',2097152-425984+1,425984,2097152)]:
 boundary_cases.append({'case':label,'held':held,'need':need,'cap':cap,'admissible':held+need<=cap})
expected=[True,True,False,False,False,True,False,True,False,True,False,True,False]
assert [c['admissible'] for c in boundary_cases]==expected
out={'status':'INDEPENDENT_ENCODING_AND_ARITHMETIC_CHECKS_PASS_NOT_RUNTIME_ACCEPTANCE','encoded_leaf_count':len(actual),'pages':40,'record_entries':1024,'support_entries':2504,'cases':boundary_cases,'unchanged_caps':r['global_caps_unchanged'],'distinct_key_index_control':g['checks'],'limitations':['Specimens are Cartesian structural maxima, not semantically coherent accepted packets.','No LifecycleCapture/session runtime implementation or native IO is exercised.','Current actual collector caps and pure arithmetic enforce admission; offered2N2max1628events is not admitted.']}
(P/'INDEPENDENT_REPLAY.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
print(json.dumps({'status':out['status'],'new_support_bytes':new,'charged_old_domain_bytes':old,'ordinary_reservation':r['regular_command_reservation'],'terminal_reservation':r['terminal_command_reservation'],'cases':len(boundary_cases)},indent=2))

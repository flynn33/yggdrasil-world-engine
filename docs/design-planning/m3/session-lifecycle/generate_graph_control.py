from pathlib import Path
import json
p=Path(__file__).parent;x=json.loads((p/'SAFE_FIELDS_AND_LIMITS.json').read_text());d=json.loads((p/'BOUND_INPUT_DOMAINS.json').read_text())
old={'PROFILE':16,'ASSESSMENT':512,'RECOVERY_DIAGNOSTIC':64,'CANONICAL_SOURCE':16,'NORMALIZATION_PROOF':8,'CORRECTION_PROOF':8,'REGISTRY_PROOF':8,'CONDITION':512,'PREDICATE_OBSERVATION':512,'RECOVERY_SAFETY':8,'TARGET_VALIDITY':264}
assert sum(old.values())==1928
next_index=0
roots=[]
for kind,limit in dict(old,**{k:v for k,v in x['support_kind_maxima'].items() if k!='SESSION_HISTORY_PAGE'}).items():
 for ordinal in range(limit):
  next_index+=1; roots.append({'kind':kind,'evidence_reference':f'ref:{next_index:06d}'})
assert len(roots)==x['page_assembly']['supporting_limit_without_pages']
records=[]
for i in range(1024):
 next_index+=1;records.append({'diagnostic_reference':f'ref:{next_index:06d}','event_id':f'ref:{next_index:06d}','local_sequence':i,'storage_status':'CONFIRMED'})
pages=[]
for i in range(x['page_assembly']['page_count']):
 next_index+=1;pages.append({'evidence_reference':f'ref:{next_index:06d}','history_evidence_reference':next(r['evidence_reference'] for r in roots if r['kind']=='SESSION_HISTORY'),'page_index':i,'record_references':records[i*64:(i+1)*64],'supporting_references':roots[i*64:(i+1)*64]})
assert len({r['evidence_reference'] for r in roots})==len(roots)
assert set((r['kind'],r['evidence_reference']) for r in roots)==set((r['kind'],r['evidence_reference']) for pg in pages for r in pg['supporting_references'])
assert len([r for pg in pages for r in pg['record_references']])==1024
encode=lambda v:json.dumps(v,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode('ascii')
m=json.loads((p/'MAXIMUM_SPECIMENS.json').read_text());assert all(len(encode(pg))<=len(encode(m['leaves']['SafeSessionHistoryPage'])) for pg in pages)
out={'status':'GENERATED_DISTINCT_KEY_INDEX_CLOSURE_CONTROL_NOT_CAPTURE_EVIDENCE','old_support_limits':old,'new_support_limits':x['support_kind_maxima'],'non_page_roots':roots,'pages':pages,'checks':{'nonpage_roots':len(roots),'page_roots':len(pages),'record_roots':len(records),'unique_aliases':next_index,'largest_actual_index_page_bytes':max(len(encode(pg)) for pg in pages),'all_nonpage_keys_indexed_exactly_once':True,'pages_never_index_themselves':True},'limitations':['Keys and CONFIRMED fields are synthetic representation controls, not authenticated storage outcomes or accepted semantic lifecycle fixtures.','This controls bounded typed index closure; semantic edges, source/math validation and actual storage ACK/unknown outcomes still require runtime owners and tests.']}
(p/'REPRESENTATION_GRAPH_CONTROL.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n');print(json.dumps(out['checks'],indent=2))

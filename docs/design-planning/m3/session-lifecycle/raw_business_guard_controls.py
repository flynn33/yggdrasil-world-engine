"""Independent JSON-size controls. This is not a production session guard."""
from pathlib import Path
import json, math
P=Path(__file__).parent
CAP=33554432
encode=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')

def compact_ascii_size(value, *, stop_after=None):
    """Exact compact JSON length, shared subtrees counted at every wire occurrence.

    On overflow return stop_after+1, never an invented exact oversize length.
    Only built-in closed JSON data accepted; no arbitrary to_record/callback.
    """
    cache={}; active=set()
    def add(a,b):
        out=a+b
        return min(out,stop_after+1) if stop_after is not None else out
    def visit(v):
        if v is None: return add(0,4)
        if type(v) is bool: return add(0,4 if v else 5)
        if type(v) in (str,int): return add(0,len(encode(v)))
        if type(v) not in (dict,list,tuple): raise ValueError('UNREGISTERED_RAW_TYPE')
        ident=id(v)
        if ident in active: raise ValueError('CYCLIC_RAW_GRAPH')
        if ident in cache: return cache[ident]
        active.add(ident)
        if type(v) is dict:
            if any(type(k) is not str for k in v): raise ValueError('NON_STRING_RAW_KEY')
            n=2
            for i,k in enumerate(sorted(v)):
                n=add(n,(1 if i else 0)+len(encode(k))+1)
                n=add(n,visit(v[k]))
                if stop_after is not None and n>stop_after: break
        else:
            n=2
            for i,z in enumerate(v):
                n=add(n,(1 if i else 0)+visit(z))
                if stop_after is not None and n>stop_after: break
        active.remove(ident); cache[ident]=n
        return n
    return visit(value)

small_cases=[None,True,False,0,18446744073709551615,'A','\u0000','\U0001f642'*512,{'b':[None,False,{'x':'\U0001f642'}],'a':(1,2,3)}]
for value in small_cases:
    assert compact_ascii_size(value)==len(encode(value))
    for limit in (1,7,64,65536):
        assert compact_ascii_size(value,stop_after=limit)==min(len(encode(value)),limit+1)
shared={'binding':{'source':'s'*256},'reason':'\U0001f642'*512}
assert compact_ascii_size([shared]*8)==len(encode([shared]*8))
cycle=[];cycle.append(cycle)
try: compact_ascii_size(cycle)
except ValueError as exc: assert str(exc)=='CYCLIC_RAW_GRAPH'
else: raise AssertionError('cycle accepted')
for value in (float('nan'),object(),{1:'bad'}):
    try: compact_ascii_size(value)
    except ValueError: pass
    else: raise AssertionError('unregistered value accepted')
# Synthetic member bytes demonstrate duplication; these are not canonical N2 witnesses.
near_cap={'payload':'x'*(CAP-1024)}
member_size=compact_ascii_size(near_cap)
assert member_size<CAP
result={'recovery_result':near_cap,'failure_detail':None}
history={'recovery_results':[near_cap],'command_results':[result]}
terminal={'full_diagnostic_chain':[near_cap,result,history]}
shapes={'individual_member':near_cap,'result_one_member':result,'history_two_copies':history,'terminal_four_copies':terminal,'eight_member_copies':[near_cap]*8}
report=[]
for name,shape in shapes.items():
    actual=compact_ascii_size(shape); measured=compact_ascii_size(shape,stop_after=CAP)
    assert measured==min(actual,CAP+1)
    report.append({'case':name,'exact_structural_bytes':actual,'bounded_measurement':measured,'wire_admissible':measured<=CAP})
assert [r['wire_admissible'] for r in report]==[True,True,False,False,False]
# Small-limit boundary controls verify exact cap, cap+1 and prospective terminal guard.
probe={'snapshot':'x'*100,'commands':[shared]};exact=compact_ascii_size(probe)
assert compact_ascii_size(probe,stop_after=exact)==exact
assert compact_ascii_size(probe,stop_after=exact-1)==exact
candidate=compact_ascii_size(result,stop_after=CAP)<=CAP
prospective_history=compact_ascii_size(history,stop_after=CAP)<=CAP
anticipated_terminal=compact_ascii_size(terminal,stop_after=CAP)<=CAP
assert candidate and not prospective_history and not anticipated_terminal
out={'status':'EXECUTED_JSON_REPRESENTATION_GUARD_CONTROLS_PASS_NOT_N3_RUNTIME_ACCEPTANCE','cap':CAP,'small_exact_cases':len(small_cases),'max512_astral_reason_encoded_bytes':len(encode('\U0001f642'*512)),'duplication_controls':report,'ordinary_decision_for_demo':'REFUSE_BEFORE_CAS_SESSION_RAW_BUSINESS_LIMIT','mandatory_halt_obligation':'Latch actual terminal mode first. Oversize canonical payload remains PendingLifecycleRecord RAW_BUSINESS_LIMIT; preserve complete immutable API-only object DAG and truthful PARTIAL persisted coverage. Guarded wire serializers refuse, never silently truncate.','limitations':['Synthetic JSON member is not an authenticated N2 RecoveryValuePacket or semantically accepted fixture.','This proves serializer arithmetic and the need for owner preflight; it does not implement or execute LifecycleCapture, session CAS, native storage, or business type serializers.','Production guard must use closed registered serializers preserving exact to_record keys/headers/flattening and all duplicate wire occurrences; never invoke arbitrary callbacks or first allocate unbounded recursive copies.','Pure size plans for future terminal closure are sizing data, not observations, ACKs, timestamps, or valid business packets.']}
(P/'RAW_BUSINESS_GUARD_CONTROLS.json').write_text(json.dumps(out,indent=2)+'\n',newline='\n')
print(json.dumps({k:out[k] for k in ('status','cap','max512_astral_reason_encoded_bytes','duplication_controls')},indent=2))

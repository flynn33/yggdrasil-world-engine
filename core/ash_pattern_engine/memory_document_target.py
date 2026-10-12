"""Bounded owned canonical memory documents with actual readback truth [YWE-REQ-0049]."""
from threading import Lock

from . import planner_emitter_values as p

_OWNER = object()
_LOCK_TYPE = type(Lock())
UINT64_MAX = (1 << 64)-1


class MemoryDocumentTarget:
    __slots__ = ("_configuration", "_cookie", "_lock", "_revision", "_documents", "_leases", "_lease_lock", "_active_leases")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("MemoryDocumentTarget is final")

    def __init__(self, configuration):
        p._exact(configuration,p.MemoryTargetConfiguration,"target.configuration")
        p.revalidate_value(configuration)
        self._configuration=configuration
        self._lock=Lock()
        self._revision=0
        self._documents={}
        self._leases=[]
        self._lease_lock=Lock()
        self._active_leases=0
        self._cookie=(_OWNER,self,configuration,self._lock,self._lease_lock,self._leases)

    def configuration(self):
        p._exact(self,MemoryDocumentTarget,"target")
        cookie=self._cookie
        if (type(cookie) is not tuple or len(cookie)!=6 or cookie[0] is not _OWNER or
                cookie[1] is not self or cookie[2] is not self._configuration or
                type(self._lock) is not _LOCK_TYPE or cookie[3] is not self._lock or
                type(self._lease_lock) is not _LOCK_TYPE or cookie[4] is not self._lease_lock or
                type(self._leases) is not list or cookie[5] is not self._leases or len(self._leases)>2048 or
                type(self._active_leases) is not int or not 0<=self._active_leases<=8 or
                type(self._revision) is not int or not 0<=self._revision<=UINT64_MAX or
                type(self._documents) is not dict or len(self._documents)>32):
            p._fail("target","VALUE_CORRUPT")
        for lease in self._leases:
            p._exact(lease,p.EmissionActionLease,"target.lease")
        for name,document in self._documents.items():
            p._exact(name,str,"target.document_name")
            p._exact(document,p.MaterializedDocument,"target.document")
            p.revalidate_value(document)
            if document.name!=name or document.creation_revision>self._revision:
                p._fail("target.document","VALUE_CORRUPT")
        p.revalidate_value(self._configuration)
        return self._configuration

    def snapshot(self):
        configuration=MemoryDocumentTarget.configuration(self)
        if not self._lock.acquire(False):
            p._fail("target.snapshot","VALUE_CORRUPT")
        try:
            return p.TargetSnapshot(configuration,self._revision,
                   tuple(self._documents[name] for name in sorted(self._documents)),
                   sum(row.actual_byte_count for row in self._documents.values()))
        finally:
            self._lock.release()

    def materialize(self, lease, description):
        configuration=MemoryDocumentTarget.configuration(self)
        operation,expected_revision=p._action_lease_facts(lease,self,description)
        p.revalidate_value(description)
        content=p.canonical_bytes(description.document).decode("ascii")
        # All lease and description primitive facts are validated and copied before target locking.
        artifact,element,plan,name,digest,count=(description.artifact_reference,description.plan_element_reference,
             description.document.plan_reference,description.name,description.content_sha256,description.content_byte_count)

        def receipt(status,effects,code,before=None,after=None,observed=None):
            return p._seal_result(p.MemoryTargetReceipt(operation,artifact,element,configuration.target_reference,status,effects,digest,
                   None if observed is None else observed.actual_sha256,count,
                   None if observed is None else observed.actual_byte_count,before,after,
                   "UNAVAILABLE" if observed is None else "OWNED_EXACT_READBACK",code),self)

        if not p._claim_action_lease(lease):
            return receipt("FAILED",False,"TARGET_RESOURCE_LIMIT")

        if not self._lease_lock.acquire(False):
            return receipt("FAILED",False,"TARGET_BUSY")
        try:
            if any(item is lease for item in self._leases) or len(self._leases)>=2048:
                return receipt("FAILED",False,"TARGET_RESOURCE_LIMIT")
            if self._active_leases>=8:
                return receipt("FAILED",False,"TARGET_BUSY")
            self._leases.append(lease)
            self._active_leases+=1
        finally:
            self._lease_lock.release()
        try:
            if not self._lock.acquire(False):
                return receipt("FAILED",False,"TARGET_BUSY")
            try:
                return _materialize_locked(self,configuration,content,artifact,element,plan,name,digest,count,expected_revision,receipt)
            finally:
                self._lock.release()
        finally:
            with self._lease_lock:
                self._active_leases-=1


def _materialize_locked(target,configuration,content,artifact,element,plan,name,digest,count,expected_revision,receipt):
    before=target._revision
    if expected_revision!=before:
        return receipt("FAILED",False,"TARGET_STALE_REVISION",before,before)
    existing=target._documents.get(name)
    if existing is not None:
        if existing.content_ascii==content and existing.plan_element_reference==element:
            return receipt("NO_EFFECT",False,None,before,before,existing)
        return receipt("FAILED",False,"DOCUMENT_CONFLICT",before,before,existing)
    if before==UINT64_MAX:
        return receipt("FAILED",False,"TARGET_VERSION_EXHAUSTED",before,before)
    used=sum(row.actual_byte_count for row in target._documents.values())
    if len(target._documents)>=configuration.max_documents or used+count>configuration.max_bytes:
        return receipt("FAILED",False,"TARGET_RESOURCE_LIMIT",before,before)
    document=p.MaterializedDocument(artifact,plan,element,name,content,digest,count,before+1)
    target._documents={**target._documents,name:document}
    target._revision=before+1
    return receipt("SUCCEEDED",True,None,before,target._revision,target._documents[name])

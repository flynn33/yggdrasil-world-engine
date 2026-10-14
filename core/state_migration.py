"""Exact schema-bound M4 decimal migration reference oracle (YWE-REQ-0054)."""

from decimal import Decimal, InvalidOperation
import hashlib
import json

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from .state_journal import JournalError, _identifier, _object_bytes


class MigrationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise MigrationError("INVALID_SOURCE")
        value[key] = item
    return value


def _number(token):
    if len(token) > 128:
        raise MigrationError("MIGRATION_LIMIT")
    number = Decimal(token)
    if not number.is_finite() or not -1024 <= number.as_tuple().exponent <= 1024:
        raise MigrationError("INVALID_SOURCE")
    return number


def _integer(token):
    if len(token.lstrip("-")) > 16:
        raise MigrationError("INVALID_SOURCE")
    value = int(token)
    if abs(value) > 9007199254740991:
        raise MigrationError("INVALID_SOURCE")
    return value


def _nonfinite(token):
    raise MigrationError("INVALID_SOURCE")


def _bounded(value):
    pending, count = [(value, 0)], 0
    while pending:
        item, depth = pending.pop()
        count += 1
        if count > 4096 or depth > 32:
            raise MigrationError("MIGRATION_LIMIT")
        if type(item) is dict:
            pending.extend((child, depth + 1) for pair in item.items() for child in pair)
        elif type(item) is list:
            pending.extend((child, depth + 1) for child in item)
        elif type(item) is str:
            item.encode("utf-8")


def _q6(value):
    if type(value) not in (int, Decimal) or not 0 <= value <= 1:
        raise MigrationError("INVALID_SOURCE")
    decimal = value if type(value) is Decimal else Decimal(value)
    sign, digits, exponent = decimal.as_tuple()
    coefficient = int("".join(map(str, digits)))
    shift = exponent + 6
    if shift >= 0:
        result = coefficient * 10 ** shift
    else:
        result, remainder = divmod(coefficient, 10 ** -shift)
        if remainder:
            raise MigrationError("UNREPRESENTABLE_SCORE")
    return -result if sign else result


def _pointer(parts):
    return "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in parts)


def _parents(value, path, prefix=()):
    if not path:
        if type(value) is not dict:
            raise MigrationError("INVALID_SOURCE")
        yield prefix, value
    elif path[0] == "*":
        if type(value) is not list:
            raise MigrationError("INVALID_SOURCE")
        for index, item in enumerate(value):
            yield from _parents(item, path[1:], (*prefix, index))
    else:
        if type(value) is not dict or path[0] not in value:
            raise MigrationError("INVALID_SOURCE")
        yield from _parents(value[path[0]], path[1:], (*prefix, path[0]))


class StateMigration:
    """Trusted immutable plan; untrusted source bytes; no publication effects."""

    def __init__(self, plan, source_schema, target_schema):
        try:
            self._plan_raw = _object_bytes(plan)
            self._plan = json.loads(self._plan_raw)
            required = {"migration_id", "source_document_id", "target_document_id", "source_schema_id",
                        "target_schema_id", "source_version", "target_version", "source_schema_sha256",
                        "target_schema_sha256", "rules"}
            if set(self._plan) != required:
                raise ValueError()
            for key in required - {"rules"}:
                _identifier(self._plan[key])
            rules = self._plan["rules"]
            if type(rules) is not list or not 1 <= len(rules) <= 32:
                raise ValueError()
            destinations = set()
            for rule in rules:
                if type(rule) is not dict or set(rule) != {"parent_path", "source_field", "target_field"}:
                    raise ValueError()
                path = rule["parent_path"]
                if type(path) is not list or len(path) > 8:
                    raise ValueError()
                for part in path:
                    if part != "*":
                        _identifier(part)
                for key in ("source_field", "target_field"):
                    _identifier(rule[key])
                    if rule[key] in ("schema_id", "schema_version"):
                        raise ValueError()
                destination = (*path, rule["target_field"])
                if destination in destinations or rule["source_field"] == rule["target_field"]:
                    raise ValueError()
                destinations.add(destination)
            validators = []
            for role, schema in (("source", source_schema), ("target", target_schema)):
                raw = _object_bytes(schema)
                schema = json.loads(raw)
                if (_digest(raw) != self._plan[role + "_schema_sha256"]
                        or schema.get("$id") != self._plan[role + "_document_id"]
                        or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"):
                    raise ValueError()
                pending = [schema]
                while pending:
                    node = pending.pop()
                    if type(node) is dict:
                        if "$ref" in node or "$dynamicRef" in node:
                            raise ValueError()
                        pending.extend(node.values())
                    elif type(node) is list:
                        pending.extend(node)
                Draft202012Validator.check_schema(schema)
                validators.append(Draft202012Validator(schema))
            self._source_validator, self._target_validator = validators
        except (JournalError, ValueError, TypeError, SchemaError, UnicodeError):
            raise MigrationError("INVALID_PLAN") from None

    def migrate(self, raw):
        if type(raw) is not bytes:
            raise MigrationError("INVALID_SOURCE")
        if len(raw) > 65536:
            raise MigrationError("MIGRATION_LIMIT")
        try:
            target = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_float=_number,
                                parse_int=_integer, parse_constant=_nonfinite)
            _bounded(target)
            if (type(target) is not dict or target.get("schema_id") != self._plan["source_schema_id"]
                    or target.get("schema_version") != self._plan["source_version"]
                    or not self._source_validator.is_valid(target)):
                raise MigrationError("INVALID_SOURCE")
            conversions = []
            for rule in self._plan["rules"]:
                for path, parent in _parents(target, rule["parent_path"]):
                    source, destination = rule["source_field"], rule["target_field"]
                    if source not in parent or destination in parent:
                        raise MigrationError("INVALID_SOURCE")
                    if len(conversions) >= 256:
                        raise MigrationError("MIGRATION_LIMIT")
                    original = parent[source]
                    converted = _q6(original)
                    conversions.append({"source_pointer": _pointer((*path, source)),
                        "target_pointer": _pointer((*path, destination)),
                        "source_decimal": str(original), "target_q6": converted})
                    del parent[source]
                    parent[destination] = converted
            target["schema_id"] = self._plan["target_schema_id"]
            target["schema_version"] = self._plan["target_version"]
            if not self._target_validator.is_valid(target):
                raise MigrationError("INVALID_TARGET")
            try:
                target_raw = _object_bytes(target)
                result = {"format": "ywe.state_migration.v1", "migration_id": self._plan["migration_id"],
                          "plan_sha256": _digest(self._plan_raw), "source_sha256": _digest(raw),
                          "target_sha256": _digest(target_raw), "target": target, "conversions": conversions}
                _object_bytes(result)
            except JournalError as error:
                raise MigrationError("MIGRATION_LIMIT" if error.code == "VALUE_LIMIT" else "INVALID_TARGET") from None
            return result
        except MigrationError:
            raise
        except (ValueError, TypeError, KeyError, UnicodeError, RecursionError, InvalidOperation):
            raise MigrationError("INVALID_SOURCE") from None

    def verify(self, raw, result):
        try:
            return _object_bytes(result) == _canonical(self.migrate(raw))
        except (MigrationError, JournalError):
            return False

"""Executable review model for two YWE value contracts; verification only.

This module is not application source and does not replace YWE's current
StateModel, diagnostics, normalization, recovery, or generation implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
from typing import Any

# Exact enumeration/order from the pinned YWE codeword-set specification.
CODEWORD_SIGNATURES: tuple[str, ...] = (
    '000000000', '000011110', '001100110', '001111000',
    '010101010', '010110100', '011001100', '011010010',
    '100101100', '100110010', '101001010', '101010100',
    '110000110', '110011000', '111100000', '111111110',
)
CODEWORD_BITS: tuple[tuple[int, ...], ...] = tuple(
    tuple(int(b) for b in s) for s in CODEWORD_SIGNATURES
)


class ContractError(ValueError):
    """Local review diagnostic, not an approved engine-wide error taxonomy."""

    def __init__(self, code: str, pointer: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.pointer = pointer

    def as_record(self) -> dict[str, str]:
        return {'code': self.code, 'instance_pointer': self.pointer,
                'message': str(self)}


def _domain_bits(bits: object) -> tuple[int, ...]:
    if type(bits) is not tuple:
        raise ContractError('VALUE_TYPE', '', 'Domain coordinates require an owned tuple.')
    if len(bits) != 9:
        raise ContractError('BIT_WIDTH', '', 'Exactly nine coordinates are required.')
    for i, b in enumerate(bits):
        if type(b) is not int or b not in (0, 1):
            raise ContractError('BIT_VALUE', f'/{i}', 'A domain coordinate is the integer 0 or 1.')
    return bits


@dataclass(frozen=True, slots=True)
class AshState:
    """A represented state, not a stability or operational-admission certificate."""

    bits: tuple[int, ...]

    def __post_init__(self) -> None:
        _domain_bits(self.bits)

    def signature(self) -> str:
        return ''.join(str(b) for b in self.bits)

    def transformed_by(self, codeword: CanonicalCodeword) -> AshState:
        if type(codeword) is not CanonicalCodeword:
            raise ContractError('CODEWORD_TYPE', '', 'A validated codeword is required.')
        return AshState(tuple(a ^ b for a, b in zip(self.bits, codeword.bits)))


@dataclass(frozen=True, slots=True)
class CanonicalCodeword:
    """Immutable exact-set member; callers cannot select another codeword set."""

    bits: tuple[int, ...]

    def __post_init__(self) -> None:
        _domain_bits(self.bits)
        if self.bits not in CODEWORD_BITS:
            raise ContractError('CODEWORD_MEMBERSHIP', '', 'The vector is not in the pinned canonical set.')

    def signature(self) -> str:
        return ''.join(str(b) for b in self.bits)

    def ordinal(self) -> int:
        return CODEWORD_BITS.index(self.bits)


class JsonValueCodec:
    """Explicit candidate wire rules; no repair or classification capability."""

    # Tool safeguard, NOT an adopted product message-size requirement.
    PROBE_INPUT_BYTE_LIMIT = 16384

    @staticmethod
    def _reject_constant(token: str) -> None:
        raise ContractError('JSON_SYNTAX', '', f'Non-JSON numeric constant: {token}')

    @staticmethod
    def _members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ContractError('DUPLICATE_KEY', '', 'Duplicate JSON object member.')
            result[key] = value
        return result

    @classmethod
    def parse_json(cls, raw: bytes | str) -> Any:
        if type(raw) not in (bytes, str):
            raise ContractError('JSON_TYPE', '', 'JSON input must be UTF-8 bytes or text.')
        try:
            encoded = raw if type(raw) is bytes else raw.encode('utf-8', errors='strict')
            if len(encoded) > cls.PROBE_INPUT_BYTE_LIMIT:
                raise ContractError('PROBE_INPUT_LIMIT', '', 'Verification-tool input budget exceeded.')
            text = encoded.decode('utf-8', errors='strict')
            # Decimal preserves distinctions that binary floating point can erase.
            return json.loads(text, parse_float=Decimal, parse_int=int,
                              parse_constant=cls._reject_constant,
                              object_pairs_hook=cls._members)
        except ContractError:
            raise
        except (UnicodeError, json.JSONDecodeError, ValueError, InvalidOperation,
                RecursionError) as exc:
            raise ContractError('JSON_SYNTAX', '', 'Invalid or unsupported JSON input.') from exc

    @staticmethod
    def _pointer(key: str) -> str:
        return '/' + key.replace('~', '~0').replace('/', '~1')

    @classmethod
    def _record(cls, obj: Any, kind: str) -> tuple[int, ...]:
        if type(obj) is not dict:
            raise ContractError('RECORD_TYPE', '', 'Expected a JSON object.')
        required = ('state_space', 'bits') + (('membership',) if kind == 'codeword' else ())
        for key in required:
            if key not in obj:
                raise ContractError('REQUIRED_FIELD', cls._pointer(key), 'Required member is absent.')
        if type(obj['state_space']) is not str or obj['state_space'] != 'F2^9':
            raise ContractError('STATE_SPACE', '/state_space', 'Expected the exact state-space label F2^9.')
        bits = cls._wire_bits(obj['bits'], '/bits')
        if kind == 'codeword':
            if bits not in CODEWORD_BITS:
                raise ContractError('CODEWORD_MEMBERSHIP', '/bits', 'Vector is not in the pinned set.')
            if obj['membership'] is not True:
                raise ContractError('MEMBERSHIP_ASSERTION', '/membership', 'Expected the Boolean true assertion.')
        extra = sorted(k for k in obj if k not in required)
        if extra:
            raise ContractError('UNKNOWN_FIELD', cls._pointer(extra[0]), 'This narrow record has no extension members.')
        return bits

    @staticmethod
    def _wire_bits(value: Any, pointer: str = '') -> tuple[int, ...]:
        if type(value) is not list:
            raise ContractError('BITS_TYPE', pointer, 'Expected an ordered JSON array.')
        if len(value) != 9:
            raise ContractError('BIT_WIDTH', pointer, 'Exactly nine coordinates are required.')
        result: list[int] = []
        for i, b in enumerate(value):
            # Explicit numeric equivalence is lossless for exact 0 and 1.
            if type(b) not in (int, float, Decimal) or b not in (0, 1):
                raise ContractError('BIT_VALUE', f'{pointer}/{i}', 'Expected a numeric value exactly equal to 0 or 1.')
            result.append(0 if b == 0 else 1)
        return tuple(result)

    @classmethod
    def state(cls, obj: Any) -> AshState:
        return AshState(cls._record(obj, 'state'))

    @classmethod
    def codeword(cls, obj: Any) -> CanonicalCodeword:
        return CanonicalCodeword(cls._record(obj, 'codeword'))

    @classmethod
    def state_signature(cls, text: Any) -> AshState:
        if type(text) is not str or len(text) != 9 or any(c not in '01' for c in text):
            raise ContractError('SIGNATURE', '', 'Expected exactly nine ASCII binary digits.')
        return AshState(tuple(int(c) for c in text))

    @classmethod
    def codeword_signature(cls, text: Any) -> CanonicalCodeword:
        state = cls.state_signature(text)
        return CanonicalCodeword(state.bits)

    @classmethod
    def codeword_sequence(cls, value: Any) -> tuple[CanonicalCodeword, ...]:
        if type(value) is not list:
            raise ContractError('SEQUENCE_TYPE', '', 'Expected an ordered JSON array.')
        result = []
        for i, item in enumerate(value):
            try:
                result.append(cls.codeword_signature(item))
            except ContractError as exc:
                raise ContractError(exc.code, f'/{i}{exc.pointer}', str(exc)) from exc
        return tuple(result)

    @staticmethod
    def state_record(value: AshState) -> dict[str, Any]:
        if type(value) is not AshState:
            raise ContractError('VALUE_TYPE', '', 'Expected AshState.')
        return {'state_space': 'F2^9', 'bits': list(value.bits)}

    @staticmethod
    def codeword_record(value: CanonicalCodeword) -> dict[str, Any]:
        if type(value) is not CanonicalCodeword:
            raise ContractError('VALUE_TYPE', '', 'Expected CanonicalCodeword.')
        return {'state_space': 'F2^9', 'bits': list(value.bits), 'membership': True}

    @classmethod
    def encode(cls, value: AshState | CanonicalCodeword) -> bytes:
        if type(value) is AshState:
            record = cls.state_record(value)
        elif type(value) is CanonicalCodeword:
            record = cls.codeword_record(value)
        else:
            raise ContractError('VALUE_TYPE', '', 'Unsupported value type.')
        # Fixed insertion order defined above; integers, compact UTF-8, no BOM/newline.
        return json.dumps(record, ensure_ascii=True, separators=(',', ':'),
                          allow_nan=False).encode('utf-8')

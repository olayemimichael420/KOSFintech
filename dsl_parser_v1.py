"""Tiny DSL semantic-declaration parser v1.

Scope:
- Parses only the canonical semantic declaration surface used by the isolated
  parser experiment.
- Performs structural validation only.
- Does not infer semantics, authorization, authority, implementation, or
  production behavior.
"""

from dataclasses import dataclass
import re


_FIELDS = {
    "PROPOSITION",
    "REQUIRES",
    "ESTABLISHES",
    "PRESERVES",
    "DOES_NOT_ESTABLISH",
}

_HEADER = re.compile(r"^DECLARATION\s+([A-Za-z_][A-Za-z0-9_]*)$")
_FIELD = re.compile(r"^([A-Z_]+)\s+(.+)$")


@dataclass(frozen=True)
class SemanticDeclaration:
    name: str
    proposition: str
    requires: tuple[str, ...] = ()
    establishes: tuple[str, ...] = ()
    preserves: tuple[str, ...] = ()
    does_not_establish: tuple[str, ...] = ()


def _value(text: str) -> str:
    text = text.strip()
    if len(text) < 2 or text[0] != '"' or text[-1] != '"':
        raise ValueError("semantic declaration values must be double-quoted")
    return text[1:-1]


def parse_declaration(source: str) -> SemanticDeclaration:
    lines = [
        line.strip()
        for line in source.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    if not lines or lines[-1] != "END":
        raise ValueError("declaration must terminate with END")

    header = _HEADER.fullmatch(lines[0])
    if header is None:
        raise ValueError("first line must be DECLARATION <name>")

    name = header.group(1)
    values: dict[str, list[str]] = {field: [] for field in _FIELDS}

    for line in lines[1:-1]:
        match = _FIELD.fullmatch(line)
        if match is None:
            raise ValueError(f"invalid declaration line: {line}")
        field, raw_value = match.groups()
        if field not in _FIELDS:
            raise ValueError(f"unsupported declaration field: {field}")
        values[field].append(_value(raw_value))

    if len(values["PROPOSITION"]) != 1:
        raise ValueError("declaration requires exactly one PROPOSITION")

    return SemanticDeclaration(
        name=name,
        proposition=values["PROPOSITION"][0],
        requires=tuple(values["REQUIRES"]),
        establishes=tuple(values["ESTABLISHES"]),
        preserves=tuple(values["PRESERVES"]),
        does_not_establish=tuple(values["DOES_NOT_ESTABLISH"]),
    )


def render_declaration(declaration: SemanticDeclaration) -> str:
    lines = [
        f"DECLARATION {declaration.name}",
        f'PROPOSITION "{declaration.proposition}"',
    ]
    for field, items in (
        ("REQUIRES", declaration.requires),
        ("ESTABLISHES", declaration.establishes),
        ("PRESERVES", declaration.preserves),
        ("DOES_NOT_ESTABLISH", declaration.does_not_establish),
    ):
        lines.extend(f'{field} "{item}"' for item in items)
    lines.append("END")
    return "\n".join(lines)


__all__ = ["SemanticDeclaration", "parse_declaration", "render_declaration"]

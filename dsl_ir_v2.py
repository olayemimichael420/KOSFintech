"""Typed semantic IR v2 built from the existing DSL declaration contract.

This module does not add DSL syntax or infer semantics.
It only gives existing declaration fields explicit IR types.
"""

from dataclasses import dataclass
from enum import Enum

from dsl_parser_v1 import SemanticDeclaration
from p3_relation_algebra import Boundary


@dataclass(frozen=True)
class PropositionIR:
    value: str


@dataclass(frozen=True)
class RequirementIR:
    value: str


@dataclass(frozen=True)
class EstablishmentIR:
    value: str


class PreservationKind(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    BOUNDARY = "BOUNDARY"


@dataclass(frozen=True)
class PreservationConstraintIR:
    value: str
    kind: PreservationKind = PreservationKind.UNRESOLVED


@dataclass(frozen=True)
class NonEstablishmentConstraintIR:
    value: str


@dataclass(frozen=True)
class BoundaryResolutionContext:
    left: str
    right: str
    scope: str

    def resolve(self, constraint: PreservationConstraintIR) -> Boundary:
        if constraint.kind is not PreservationKind.BOUNDARY:
            raise ValueError("constraint is not a boundary preservation constraint")
        return Boundary(self.left, self.right, self.scope)


@dataclass(frozen=True)
class CompiledPreservationIR:
    constraint: PreservationConstraintIR
    boundary: Boundary


@dataclass(frozen=True)
class SemanticIR:
    name: str
    proposition: PropositionIR
    requires: tuple[RequirementIR, ...] = ()
    establishes: tuple[EstablishmentIR, ...] = ()
    preserves: tuple[PreservationConstraintIR, ...] = ()
    does_not_establish: tuple[NonEstablishmentConstraintIR, ...] = ()


def resolve_preservation(value: str) -> PreservationConstraintIR:
    if value == "tenant boundary":
        return PreservationConstraintIR(value, PreservationKind.BOUNDARY)
    return PreservationConstraintIR(value, PreservationKind.UNRESOLVED)


def declaration_to_ir(declaration: SemanticDeclaration) -> SemanticIR:
    return SemanticIR(
        name=declaration.name,
        proposition=PropositionIR(declaration.proposition),
        requires=tuple(RequirementIR(value) for value in declaration.requires),
        establishes=tuple(EstablishmentIR(value) for value in declaration.establishes),
        preserves=tuple(resolve_preservation(value) for value in declaration.preserves),
        does_not_establish=tuple(
            NonEstablishmentConstraintIR(value)
            for value in declaration.does_not_establish
        ),
    )


def compile_preservations(
    ir: SemanticIR,
    context: BoundaryResolutionContext,
) -> tuple[CompiledPreservationIR, ...]:
    return tuple(
        CompiledPreservationIR(constraint, context.resolve(constraint))
        for constraint in ir.preserves
        if constraint.kind is PreservationKind.BOUNDARY
    )


def resolve_boundaries(
    ir: SemanticIR,
    context: BoundaryResolutionContext,
) -> tuple[Boundary, ...]:
    return tuple(
        context.resolve(constraint)
        for constraint in ir.preserves
        if constraint.kind is PreservationKind.BOUNDARY
    )


def parse_to_ir(source: str) -> SemanticIR:
    from dsl_parser_v1 import parse_declaration

    return declaration_to_ir(parse_declaration(source))


__all__ = [
    "PropositionIR",
    "RequirementIR",
    "EstablishmentIR",
    "PreservationKind",
    "PreservationConstraintIR",
    "resolve_preservation",
    "NonEstablishmentConstraintIR",
    "BoundaryResolutionContext",
    "CompiledPreservationIR",
    "SemanticIR",
    "declaration_to_ir",
    "parse_to_ir",
    "resolve_boundaries",
    "compile_preservations",
]

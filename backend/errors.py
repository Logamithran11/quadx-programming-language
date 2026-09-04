"""
QXL Error System
================
Defines all error types used across the compiler pipeline.
Each error captures the phase, message, line number, and column
for precise diagnostics in the IDE.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any


class CompilerPhase(Enum):
    """Enumeration of compiler pipeline phases."""
    LEXER = "Lexical Analysis"
    PARSER = "Syntax Analysis"
    SEMANTIC = "Semantic Analysis"
    INTERMEDIATE = "Intermediate Code Generation"
    GENERATOR = "Code Generation"
    EXECUTOR = "Execution"


@dataclass
class QXLError:
    """Base error class for all QXL compiler errors.
    
    Attributes:
        message: Human-readable error description.
        phase: The compiler phase where the error occurred.
        line: Source line number (1-indexed).
        column: Source column number (1-indexed).
        suggestion: Optional fix suggestion for IDE display.
    """
    message: str
    phase: CompilerPhase
    line: int = 0
    column: int = 0
    suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize error for JSON API response."""
        return {
            "message": self.message,
            "phase": self.phase.value,
            "line": self.line,
            "column": self.column,
            "suggestion": self.suggestion,
            "severity": "error"
        }

    def __str__(self) -> str:
        loc = f" at line {self.line}" if self.line else ""
        col = f", column {self.column}" if self.column else ""
        return f"[{self.phase.value}]{loc}{col}: {self.message}"


@dataclass
class LexerError(QXLError):
    """Error during lexical analysis (illegal characters, malformed tokens)."""
    def __init__(self, message: str, line: int = 0, column: int = 0,
                 suggestion: str = "") -> None:
        super().__init__(
            message=message,
            phase=CompilerPhase.LEXER,
            line=line,
            column=column,
            suggestion=suggestion
        )


@dataclass
class ParserError(QXLError):
    """Error during syntax analysis (unexpected tokens, missing constructs)."""
    def __init__(self, message: str, line: int = 0, column: int = 0,
                 suggestion: str = "") -> None:
        super().__init__(
            message=message,
            phase=CompilerPhase.PARSER,
            line=line,
            column=column,
            suggestion=suggestion
        )


@dataclass
class SemanticError(QXLError):
    """Error during semantic analysis (type mismatches, undefined references)."""
    def __init__(self, message: str, line: int = 0, column: int = 0,
                 suggestion: str = "") -> None:
        super().__init__(
            message=message,
            phase=CompilerPhase.SEMANTIC,
            line=line,
            column=column,
            suggestion=suggestion
        )


@dataclass
class CodeGenError(QXLError):
    """Error during code generation."""
    def __init__(self, message: str, line: int = 0, column: int = 0,
                 suggestion: str = "") -> None:
        super().__init__(
            message=message,
            phase=CompilerPhase.GENERATOR,
            line=line,
            column=column,
            suggestion=suggestion
        )


@dataclass
class ExecutionError(QXLError):
    """Error during execution of generated code."""
    def __init__(self, message: str, line: int = 0, column: int = 0,
                 suggestion: str = "") -> None:
        super().__init__(
            message=message,
            phase=CompilerPhase.EXECUTOR,
            line=line,
            column=column,
            suggestion=suggestion
        )


class ErrorCollector:
    """Collects errors across all compiler phases.
    
    Provides a centralized error registry that each compiler phase
    can append errors to. Supports filtering by phase and severity.
    
    Example:
        >>> collector = ErrorCollector()
        >>> collector.add(LexerError("Illegal character '@'", line=5))
        >>> collector.has_errors()
        True
        >>> collector.get_errors_for_phase(CompilerPhase.LEXER)
        [LexerError(...)]
    """

    def __init__(self) -> None:
        self._errors: List[QXLError] = []
        self._warnings: List[QXLError] = []

    def add(self, error: QXLError) -> None:
        """Add an error to the collection."""
        self._errors.append(error)

    def add_warning(self, warning: QXLError) -> None:
        """Add a warning (non-fatal) to the collection."""
        self._warnings.append(warning)

    def has_errors(self) -> bool:
        """Check if any errors have been recorded."""
        return len(self._errors) > 0

    def has_errors_in_phase(self, phase: CompilerPhase) -> bool:
        """Check if errors exist for a specific phase."""
        return any(e.phase == phase for e in self._errors)

    def get_errors(self) -> List[QXLError]:
        """Return all collected errors."""
        return list(self._errors)

    def get_errors_for_phase(self, phase: CompilerPhase) -> List[QXLError]:
        """Return errors filtered by compiler phase."""
        return [e for e in self._errors if e.phase == phase]

    def get_warnings(self) -> List[QXLError]:
        """Return all collected warnings."""
        return list(self._warnings)

    def clear(self) -> None:
        """Clear all errors and warnings."""
        self._errors.clear()
        self._warnings.clear()

    def to_list(self) -> List[Dict[str, Any]]:
        """Serialize all errors for JSON API response."""
        result = [e.to_dict() for e in self._errors]
        for w in self._warnings:
            d = w.to_dict()
            d["severity"] = "warning"
            result.append(d)
        return result

    @property
    def count(self) -> int:
        """Total number of errors."""
        return len(self._errors)

    def __len__(self) -> int:
        return len(self._errors)

    def __repr__(self) -> str:
        return f"ErrorCollector(errors={len(self._errors)}, warnings={len(self._warnings)})"

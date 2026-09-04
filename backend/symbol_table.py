"""
QXL Symbol Table
================
Manages symbol storage with lexical scoping for the semantic analyzer.

Supports:
    - Nested scope stack (global → function → block)
    - Variable symbols with type, initialization status, and source location
    - Function symbols with parameter types and return tracking
    - Scope-chain lookup for variable resolution
    - Serialization to dict for the IDE's symbol table display

Usage:
    >>> table = SymbolTable()
    >>> table.push_scope("global")
    >>> table.declare("x", Symbol(name="x", sym_type="number", line=1))
    >>> table.lookup("x")
    Symbol(name='x', sym_type='number', ...)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Symbol:
    """Represents a variable in the symbol table.
    
    Attributes:
        name: Variable identifier.
        sym_type: QXL type ("number", "decimal", "text", "bool").
        scope: Name of the scope where declared.
        line: Source line of declaration.
        column: Source column of declaration.
        initialized: Whether the variable has been assigned a value.
    """
    name: str
    sym_type: str
    scope: str = "global"
    line: int = 0
    column: int = 0
    initialized: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON API response."""
        return {
            "name": self.name,
            "type": self.sym_type,
            "scope": self.scope,
            "line": self.line,
            "column": self.column,
            "initialized": self.initialized,
            "kind": "variable",
        }


@dataclass
class FunctionSymbol:
    """Represents a function in the symbol table.
    
    Attributes:
        name: Function identifier.
        params: List of (param_name, param_type) tuples.
        line: Source line of declaration.
        has_return: Whether the function contains a return statement.
    """
    name: str
    params: List[tuple] = field(default_factory=list)
    line: int = 0
    has_return: bool = False

    @property
    def param_count(self) -> int:
        """Number of parameters."""
        return len(self.params)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON API response."""
        return {
            "name": self.name,
            "params": [{"name": p[0], "type": p[1]} for p in self.params],
            "param_count": self.param_count,
            "line": self.line,
            "has_return": self.has_return,
            "kind": "function",
        }


class Scope:
    """A single scope level containing variable declarations.
    
    Scopes form a stack (managed by SymbolTable). Each scope has
    a name (e.g., "global", "function:add", "if:3") and a dict
    of symbols declared within it.
    """

    def __init__(self, name: str, parent: Optional[Scope] = None) -> None:
        self.name = name
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}

    def declare(self, name: str, symbol: Symbol) -> bool:
        """Declare a symbol in this scope. Returns False if duplicate."""
        if name in self.symbols:
            return False
        self.symbols[name] = symbol
        return True

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up a symbol in this scope only (no parent chain)."""
        return self.symbols.get(name)

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol, traversing the parent chain."""
        sym = self.symbols.get(name)
        if sym is not None:
            return sym
        if self.parent is not None:
            return self.parent.lookup(name)
        return None


class SymbolTable:
    """Manages a stack of scopes for lexical scoping.
    
    The table starts with a global scope. Function bodies, if blocks,
    and repeat loops push/pop their own scopes.
    """

    def __init__(self) -> None:
        self._scopes: List[Scope] = []
        self._functions: Dict[str, FunctionSymbol] = {}
        self._all_symbols: List[Symbol] = []
        self._all_function_symbols: List[FunctionSymbol] = []
        # Initialize global scope
        self.push_scope("global")

    # ── Scope Management ────────────────────────────────────────

    def push_scope(self, name: str) -> None:
        """Push a new scope onto the stack."""
        parent = self._scopes[-1] if self._scopes else None
        self._scopes.append(Scope(name=name, parent=parent))

    def pop_scope(self) -> Optional[Scope]:
        """Pop the current scope from the stack."""
        if len(self._scopes) > 1:
            return self._scopes.pop()
        return None  # Never pop the global scope

    @property
    def current_scope(self) -> Scope:
        """Return the current (top-of-stack) scope."""
        return self._scopes[-1]

    @property
    def current_scope_name(self) -> str:
        """Return the name of the current scope."""
        return self._scopes[-1].name

    # ── Variable Operations ─────────────────────────────────────

    def declare(self, name: str, symbol: Symbol) -> bool:
        """Declare a variable in the current scope.
        
        Returns False if the variable is already declared in this scope.
        """
        symbol.scope = self.current_scope_name
        success = self.current_scope.declare(name, symbol)
        if success:
            self._all_symbols.append(symbol)
        return success

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a variable by traversing the scope chain."""
        return self.current_scope.lookup(name)

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up a variable in the current scope only."""
        return self.current_scope.lookup_local(name)

    def mark_initialized(self, name: str) -> None:
        """Mark a variable as initialized (assigned a value)."""
        sym = self.lookup(name)
        if sym is not None:
            sym.initialized = True

    # ── Function Operations ─────────────────────────────────────

    def declare_function(self, func: FunctionSymbol) -> bool:
        """Register a function declaration.
        
        Returns False if a function with the same name already exists.
        """
        if func.name in self._functions:
            return False
        self._functions[func.name] = func
        self._all_function_symbols.append(func)
        return True

    def lookup_function(self, name: str) -> Optional[FunctionSymbol]:
        """Look up a function by name."""
        return self._functions.get(name)

    # ── Serialization ───────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire symbol table for the API."""
        return {
            "variables": [s.to_dict() for s in self._all_symbols],
            "functions": [f.to_dict() for f in self._all_function_symbols],
            "scope_count": len(self._scopes),
            "variable_count": len(self._all_symbols),
            "function_count": len(self._all_function_symbols),
        }

    def get_all_symbols(self) -> List[Symbol]:
        """Return all declared variable symbols."""
        return list(self._all_symbols)

    def get_all_functions(self) -> List[FunctionSymbol]:
        """Return all declared function symbols."""
        return list(self._all_function_symbols)

    def __repr__(self) -> str:
        return (f"SymbolTable(scopes={len(self._scopes)}, "
                f"vars={len(self._all_symbols)}, "
                f"funcs={len(self._all_function_symbols)})")

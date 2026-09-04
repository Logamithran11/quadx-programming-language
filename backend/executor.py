"""
QXL Executor
=============
Executes the generated Python code in a sandboxed subprocess.

Features:
    - Subprocess isolation (no access to compiler internals)
    - Configurable timeout (default: 5 seconds)
    - Captures stdout and stderr separately
    - Reports execution time and exit code
    - Handles runtime errors gracefully

Usage:
    >>> from backend.executor import QXLExecutor
    >>> executor = QXLExecutor()
    >>> result = executor.execute("generated/output.py")
    >>> print(result["output"])
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from typing import Any, Dict, Optional

from backend.errors import ExecutionError, ErrorCollector
from backend.utils import get_generated_dir


class QXLExecutor:
    """Executes generated Python code in a subprocess.
    
    Provides sandboxed execution with timeout protection and
    comprehensive result reporting.
    """

    DEFAULT_TIMEOUT: int = 5   # seconds

    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self.errors: ErrorCollector = ErrorCollector()
        self._last_result: Dict[str, Any] = {}

    def execute(self, filepath: Optional[str] = None,
                code: Optional[str] = None,
                user_input: str = "") -> Dict[str, Any]:
        """Execute Python code and capture results.
        
        Args:
            filepath: Path to a .py file to execute (default: generated/output.py).
            code: Raw Python code string (used if filepath is None).
            user_input: Simulated stdin input for `input()` calls.
            
        Returns:
            Dict with keys: output, errors, exit_code, execution_time_ms, success.
        """
        self.errors = ErrorCollector()

        # Determine what to execute
        if filepath is None and code is None:
            filepath = os.path.join(get_generated_dir(), "output.py")

        if filepath and not os.path.exists(filepath):
            self.errors.add(ExecutionError(
                f"Generated file not found: {filepath}",
                suggestion="Compile the program first to generate output.py"
            ))
            return self._error_result("File not found")

        try:
            start_time = time.perf_counter()

            if code is not None:
                # Execute from string
                cmd = [sys.executable, "-c", code]
            else:
                # Execute from file
                cmd = [sys.executable, filepath]

            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self.timeout,
                input=user_input if user_input else None,
                cwd=get_generated_dir(),
                env=env,
            )

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            output = result.stdout
            error_output = result.stderr

            if result.returncode != 0 and error_output:
                # Parse Python traceback for user-friendly error
                friendly_error = self._parse_python_error(error_output)
                self.errors.add(ExecutionError(friendly_error))

            self._last_result = {
                "output": output,
                "errors": error_output,
                "exit_code": result.returncode,
                "execution_time_ms": elapsed_ms,
                "success": result.returncode == 0,
            }

        except subprocess.TimeoutExpired:
            self.errors.add(ExecutionError(
                f"Execution timed out after {self.timeout} seconds",
                suggestion="Check for infinite loops in your program"
            ))
            self._last_result = self._error_result(
                f"Timeout: exceeded {self.timeout}s limit"
            )

        except Exception as e:
            self.errors.add(ExecutionError(f"Execution failed: {str(e)}"))
            self._last_result = self._error_result(str(e))

        return self._last_result

    def get_last_result(self) -> Dict[str, Any]:
        """Return the result of the last execution."""
        return self._last_result

    def _error_result(self, message: str) -> Dict[str, Any]:
        """Build a standardized error result dict."""
        return {
            "output": "",
            "errors": message,
            "exit_code": 1,
            "execution_time_ms": 0,
            "success": False,
        }

    def _parse_python_error(self, traceback: str) -> str:
        """Extract a user-friendly error message from a Python traceback."""
        lines = traceback.strip().split("\n")
        if lines:
            # Last line usually contains the actual error
            error_line = lines[-1]
            # Remove "Traceback (most recent call last):" prefix variations
            for prefix in ["NameError:", "TypeError:", "ValueError:",
                           "ZeroDivisionError:", "IndexError:",
                           "RuntimeError:", "SyntaxError:"]:
                if prefix in error_line:
                    return error_line.strip()
            return error_line.strip()
        return traceback.strip()

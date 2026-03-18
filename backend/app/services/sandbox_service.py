import subprocess
import tempfile
import os
import sys
import logging
import ast
from pathlib import Path

logger = logging.getLogger(__name__)


class SandboxService:
    @staticmethod
    def execute_code(code: str, file_path: str):
        try:
            with tempfile.TemporaryDirectory() as work_dir:
                work_dir = Path(work_dir)
                script_path = work_dir / "execute.py"

                abs_file_path = Path(file_path).as_posix() if file_path else ""
                script_content = f'''
import pandas as pd
import json

# 执行用户代码
file_path = r"{abs_file_path}"
user_code = {code!r}

sandbox_vars = {{}}
exec(user_code, {{
    "pd": pd,
    "file_path": file_path,
    "__name__": "__main__"
}}, sandbox_vars)

result = sandbox_vars.get("result", "执行成功")
chart_json = sandbox_vars.get("chart_json", {{}})

print("__SANDBOX_RESULT__", {{"result": result, "chart_json": chart_json}})
'''

                script_path.write_text(script_content, encoding="utf-8")

                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    cwd=str(work_dir),
                )

                output = {"result": "", "chart_json": {}}
                for line in result.stdout.splitlines():
                    if "__SANDBOX_RESULT__" in line:
                        output = ast.literal_eval(
                            line.replace("__SANDBOX_RESULT__", "").strip()
                        )

                return {
                    "success": result.returncode == 0,
                    "output": output,
                    "errors": [result.stderr] if result.returncode != 0 else [],
                }

        except Exception as e:
            return {"success": False, "output": {}, "errors": [str(e)]}

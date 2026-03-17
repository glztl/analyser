import subprocess
import tempfile
import os
import sys
import logging
import ast
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)


class SandboxService:
    @staticmethod
    def execute_code(code: str, file_path: str):
        try:
            with tempfile.TemporaryDirectory() as work_dir:
                work_dir = Path(work_dir)
                script_path = work_dir / "execute.py"

                output_dir = Path(settings.SANDBOX_OUTPUT_DIR)
                output_dir.mkdir(exist_ok=True)

                # ✅ 最终版脚本（Agg 后端 + 绝对路径）
                script_content = f'''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import os

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
plt.rcParams['font.family'] = 'sans-serif'

# 绝对路径
OUTPUT_DIR = r"{output_dir.absolute().as_posix()}"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_chart(filename):
    full_path = os.path.abspath(os.path.join(OUTPUT_DIR, filename))
    plt.savefig(full_path, bbox_inches='tight', dpi=150)
    plt.close()
    return full_path

file_path = r"{file_path}"
df = pd.read_excel(file_path)

# 执行用户代码
user_code = {code!r}
sandbox_vars = {{
    "pd": pd,
    "plt": plt,
    "df": df,
    "file_path": file_path,
    "save_chart": save_chart
}}
exec(user_code, sandbox_vars)

# 输出结果
result = sandbox_vars.get("result", "执行成功")
chart_path = sandbox_vars.get("chart_path", "")
print("__SANDBOX_RESULT__", {{"result": result, "chart_path": chart_path}})
'''

                script_path.write_text(script_content, encoding="utf-8")

                # 执行
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(work_dir),
                )

                output = {"result": "", "chart_path": ""}
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

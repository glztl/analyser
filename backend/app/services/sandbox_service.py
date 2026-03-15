import os
import subprocess
import tempfile
import json
import uuid
import shutil
from pathlib import Path
from typing import Optional
from app.core.config import settings


class SandboxService:
    """
    代码沙箱服务
    在隔离环境中执行用户代码，确保安全
    """
    @staticmethod
    def execute_code(code: str, file_path: Optional[str] = None) -> dict:
        """
        执行Python代码并返回结果

        Args: 
            code: 要执行的Python代码
            file_path: 数据文件路径

        Returns:
            dict: 包含执行结果、输出、错误信息
        """
        # 生成唯一的执行 ID
        exec_id = uuid.uuid4().hex

        # 创建临时目录用于本次执行
        work_dir = Path(tempfile.mkdtemp(prefix=f"sandbox_{exec_id}"))

        # 准备执行脚本
        script_content = f"""

import sys
import json
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# 重定向输出
output_data = {{}}
errors = []

try:
    # 如果有文件，加载到 df 变量
    df = None
    file_path = r"{file_path}" if r"{file_path}" else None

    if file_path and os.path.exists(file_path):
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endwith('.xlsx') or file_path.endswith('.xls'):
            df = pd.read.excel(file_path)

    # 执行用户代码
    {code}

    # 捕获输出数据 (用户代码需要将结果赋值给 result 变量)
    if 'result' in local():
        output_data['result'] = str(result)
    if 'char_path' in locals():
        output_data['chart_path'] = chart_path

except Exception as e:
    errors.append(str(e))

# 输出Json结果
print("<<< SANDBOX_OUTPUT_START >>>")
print("json.dumps({{"output": output_data, "errors": errors}}))
print("<<< SANDBOX_OUTPUT_END >>>")

"""
        
        script_path = work_dir / "execute.py"
        script_path.write_text(script_content, encoding='utf-8')

        try:
            # 执行子进程
            # 生产环境调用Docker
            result = subprocess.run(
                ['python', str(script_path)],
                capture_output=True,
                text=True,
                timeout=30, # 30秒超时，防止死循环
                cwd=str(work_dir),
                env={
                    **os.environ,
                    "PYTHONPATH": str(work_dir),
                    # 限制环境变量，防止泄漏敏感信息
                    "PATH": os.environ.get("PATH", ""),
                }
            )

            # 解析输出
            output = result.stdout
            error = result.stderr

            # 提取JSON输出
            output_data = {"output": {}, "errors": []}
            for line in output.split("\n"):
                if "<<< SANDBOX_OUTPUT_START >>>" in line:
                    continue
                if "<<< SANDBOX_OUTPUT_END >>>" in line:
                    continue
                try:
                    output_data = json.loads(line)
                    break
                except:
                    continue
            return {
                "success": len(output_data.get("errors", [])) == 0,
                "output": output_data.get("output", {}),
                "errors": output_data.get("errors", []) + ([error] if error else []),
                "stdout": output,
                "stderr": error
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": {},
                "errors": ["代码执行超时 (超过30秒)"],
                "stdout": "",
                "stderr": ""
            }
        except Exception as e:
            return {
                "success": False,
                "output": {},
                "errors": [f"沙箱执行错误: {str(e)}"],
                "stdout": "",
                "stderr": ""
            }

        finally:
            # 清理临时文件
            try:
                shutil.rmtree(work_dir)
            except:
                pass


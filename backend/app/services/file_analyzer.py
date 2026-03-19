import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
import chardet  # 用于检测 CSV 编码
import logging

logger = logging.getLogger(__name__)


class FileAnalyzer:
    """
    文件结构分析器
    在 LLM 生成代码前，先分析文件结构和数据特征
    """

    @staticmethod
    def analyze_file(file_path: str) -> Dict[str, Any]:
        """
        分析文件结构，返回结构化信息

        Returns:
            dict: 包含文件结构、数据特征、安全信息
        """
        path = Path(file_path)

        # ========== 1. 基础信息 ==========
        file_info = {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "size_bytes": path.stat().st_size,
            "size_human": FileAnalyzer._format_size(path.stat().st_size),
        }

        # ========== 2. 安全检查 ==========
        security_check = FileAnalyzer._security_check(path)
        if not security_check["safe"]:
            return {
                "success": False,
                "error": security_check["error"],
                "security": security_check,
            }

        # ========== 3. 数据读取与结构分析 ==========
        try:
            df = FileAnalyzer._read_file(path)
        except Exception as e:
            return {
                "success": False,
                "error": f"文件读取失败：{str(e)}",
                "file_info": file_info,
            }

        # ========== 4. 结构分析 ==========
        structure = {
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "columns": FileAnalyzer._analyze_columns(df),
            "index_type": FileAnalyzer._detect_index_type(df),
            "table_orientation": FileAnalyzer._detect_orientation(df),
        }

        # ========== 5. 数据质量分析 ==========
        quality = FileAnalyzer._analyze_quality(df)

        # ========== 6. 数据特征分析 ==========
        features = FileAnalyzer._analyze_features(df)

        # ========== 7. 分析策略推荐 ==========
        strategy = FileAnalyzer._recommend_strategy(df, structure, quality)

        # ========== 8. 生成 LLM 可用的上下文 ==========
        llm_context = FileAnalyzer._generate_llm_context(
            df, structure, quality, strategy
        )

        # ========== 9. 预览数据（前 5 行） ==========
        preview = {
            "headers": df.columns.tolist(),
            "rows": df.head(5).fillna(None).to_dict(orient="records"),
        }

        return {
            "success": True,
            "file_info": file_info,
            "security": security_check,
            "structure": structure,
            "quality": quality,
            "features": features,
            "strategy": strategy,
            "llm_context": llm_context,
            "preview": preview,
        }

    @staticmethod
    def _format_size(size_bytes: int | float) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"

    @staticmethod
    def _security_check(path: Path) -> Dict[str, Any]:
        """安全检查"""
        # 检查文件扩展名
        allowed_extensions = {".csv", ".xlsx", ".xls", ".xlsm"}
        if path.suffix.lower() not in allowed_extensions:
            return {"safe": False, "error": f"不支持的文件类型：{path.suffix}"}

        # 检查文件大小（最大 50MB）
        max_size = 50 * 1024 * 1024
        if path.stat().st_size > max_size:
            return {
                "safe": False,
                "error": f"文件过大：{FileAnalyzer._format_size(path.stat().st_size)}，最大支持 50MB",
            }

        # Excel 文件检查宏
        if path.suffix.lower() in {".xlsm", ".xltm"}:
            return {"safe": False, "error": "不支持带宏的 Excel 文件，可能存在安全风险"}

        return {"safe": True}

    @staticmethod
    def _read_file(path: Path) -> pd.DataFrame:
        """读取文件"""
        if path.suffix.lower() == ".csv":
            # 自动检测编码
            with open(path, "rb") as f:
                encoding = chardet.detect(f.read(10000))["encoding"] or "utf-8"
            return pd.read_csv(path, encoding=encoding, on_bad_lines="skip")
        elif path.suffix.lower() in {".xlsx", ".xlsm"}:
            return pd.read_excel(path, engine="openpyxl")
        elif path.suffix.lower() == ".xls":
            return pd.read_excel(path, engine="xlrd")
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

    @staticmethod
    def _analyze_columns(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """分析每列的特征"""
        columns_info = []

        for col in df.columns:
            col_data = df[col]
            col_info = {
                "name": str(col),
                "dtype": str(col_data.dtype),
                "non_null_count": int(col_data.notna().sum()),
                "null_count": int(col_data.isna().sum()),
                "null_percentage": round(col_data.isna().mean() * 100, 2),
                "unique_count": int(col_data.nunique()),
                "is_numeric": pd.api.types.is_numeric_dtype(col_data),
                "is_datetime": pd.api.types.is_datetime64_any_dtype(col_data),
                "is_categorical": col_data.nunique() / len(col_data) < 0.1
                if len(col_data) > 0
                else False,
            }

            # 数值列的统计信息
            if col_info["is_numeric"]:
                numeric_data = pd.to_numeric(col_data, errors="coerce")
                col_info["stats"] = {
                    "min": float(numeric_data.min())
                    if not numeric_data.isna().all()
                    else None,
                    "max": float(numeric_data.max())
                    if not numeric_data.isna().all()
                    else None,
                    "mean": float(numeric_data.mean())
                    if not numeric_data.isna().all()
                    else None,
                    "std": float(numeric_data.std())
                    if not numeric_data.isna().all()
                    else None,
                }

            # 示例值
            col_info["sample_values"] = col_data.dropna().head(3).tolist()

            columns_info.append(col_info)

        return columns_info

    @staticmethod
    def _detect_index_type(df: pd.DataFrame) -> str:
        """检测索引类型（时间序列、类别等）"""
        if len(df.columns) == 0:
            return "unknown"

        first_col = df.iloc[:, 0]

        # 检查是否是时间序列
        if pd.api.types.is_datetime64_any_dtype(first_col):
            return "datetime"

        # 检查是否是连续数字（可能是 ID）
        if pd.api.types.is_numeric_dtype(first_col):
            if first_col.nunique() == len(first_col):
                return "id"

        # 检查是否是类别
        if first_col.dtype == "object" and first_col.nunique() < len(first_col) * 0.5:
            return "categorical"

        return "general"

    @staticmethod
    def _detect_orientation(df: pd.DataFrame) -> str:
        """检测表格方向（横向宽表 vs 纵向长表）"""
        if len(df) == 0 or len(df.columns) == 0:
            return "unknown"

        # 横向宽表：行数少，列数多，第一列可能是指标名
        if len(df) <= 20 and len(df.columns) > 10:
            return "wide"  # 宽表

        # 纵向长表：行数多，列数适中
        if len(df) > 50 and len(df.columns) <= 20:
            return "long"  # 长表

        # 检查第一列是否是文本（可能是指标名）
        if df.iloc[:, 0].dtype == "object" and df.iloc[:, 0].nunique() < len(df) * 0.3:
            return "wide"

        return "long"

    @staticmethod
    def _analyze_quality(df: pd.DataFrame) -> Dict[str, Any]:
        """数据质量分析"""
        total_cells = df.size
        null_cells = df.isnull().sum().sum()

        # 检测重复行
        duplicate_rows = df.duplicated().sum()

        # 检测异常值（数值列）
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outliers_count = 0
        for col in numeric_cols:
            if len(df[col]) > 0:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                outliers = (
                    (df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)
                ).sum()
                outliers_count += outliers

        completeness = (1 - null_cells / total_cells) * 100 if total_cells > 0 else 0

        # 质量评分
        score = 100
        if completeness < 80:
            score -= 20
        elif completeness < 95:
            score -= 10

        if duplicate_rows > len(df) * 0.1:
            score -= 15

        if outliers_count > total_cells * 0.05:
            score -= 10

        return {
            "completeness": round(completeness, 2),
            "null_cells": int(null_cells),
            "duplicate_rows": int(duplicate_rows),
            "outliers_count": int(outliers_count),
            "quality_score": max(0, score),
            "quality_level": "优秀"
            if score >= 90
            else "良好"
            if score >= 70
            else "需清理",
        }

    @staticmethod
    def _analyze_features(df: pd.DataFrame) -> Dict[str, Any]:
        """数据特征分析"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()
        datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

        # 检测可能的指标列和维度列
        potential_metrics = []
        potential_dimensions = []

        for col in df.columns:
            col_data = df[col]
            if pd.api.types.is_numeric_dtype(col_data):
                # 数值列，可能是指标
                if col_data.nunique() > len(df) * 0.5:  # 唯一值多
                    potential_metrics.append(col)
                else:
                    potential_dimensions.append(col)
            else:
                potential_dimensions.append(col)

        return {
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "datetime_columns": datetime_cols,
            "potential_metrics": potential_metrics,
            "potential_dimensions": potential_dimensions,
            "correlation_matrix": df[numeric_cols].corr().to_dict()
            if len(numeric_cols) > 1
            else None,
        }

    @staticmethod
    def _recommend_strategy(
        df: pd.DataFrame, structure: Dict, quality: Dict
    ) -> Dict[str, Any]:
        """推荐分析策略"""
        num_rows = structure["num_rows"]
        orientation = structure["table_orientation"]

        # 根据数据规模推荐
        if num_rows <= 10:
            strategy_type = "detailed"
            description = "数据量较小，适合详细分析每个指标"
            max_series = num_rows
        elif num_rows <= 50:
            strategy_type = "top_n"
            description = f"数据量适中，展示 Top 10 指标（共 {num_rows} 个）"
            max_series = 10
        elif num_rows <= 200:
            strategy_type = "statistical"
            description = "数据量较大，建议关注统计特征和分布"
            max_series = 5
        else:
            strategy_type = "summary"
            description = f"数据量很大（{num_rows} 行），建议使用聚合或抽样分析"
            max_series = 0

        # 根据质量调整
        if quality["quality_score"] < 70:
            description += " ⚠️ 数据质量较低，建议先清理"

        return {
            "type": strategy_type,
            "description": description,
            "max_series": max_series,
            "recommended_charts": FileAnalyzer._recommend_charts(df, orientation),
        }

    @staticmethod
    def _recommend_charts(df: pd.DataFrame, orientation: str) -> List[str]:
        """推荐图表类型"""
        charts = []

        if orientation == "wide":
            charts.extend(["multi_line", "radar", "heatmap"])
        else:
            charts.extend(["bar", "scatter", "boxplot"])

        # 有时间列推荐折线图
        datetime_cols = df.select_dtypes(include=["datetime64"]).columns
        if len(datetime_cols) > 0:
            charts.insert(0, "line")

        return charts[:3]  # 只返回前 3 个推荐

    @staticmethod
    def _generate_llm_context(
        df: pd.DataFrame, structure: Dict, quality: Dict, strategy: Dict
    ) -> str:
        """生成 LLM 可用的上下文信息"""
        context = f"""
# 文件结构分析

## 基础信息
- 行数：{structure["num_rows"]}
- 列数：{structure["num_columns"]}
- 表格方向：{structure["table_orientation"]}（{"宽表：第一列可能是指标名" if structure["table_orientation"] == "wide" else "长表：每行是一条记录"}）

## 列信息
"""
        for col_info in structure["columns"][:10]:  # 只展示前 10 列
            context += f"- `{col_info['name']}`: {col_info['dtype']}"
            if col_info["is_numeric"] and col_info.get("stats"):
                context += (
                    f" (范围：{col_info['stats']['min']} ~ {col_info['stats']['max']})"
                )
            if col_info["null_percentage"] > 0:
                context += f" 缺失率：{col_info['null_percentage']}%"
            context += "\n"

        if len(structure["columns"]) > 10:
            context += f"- ... 还有 {len(structure['columns']) - 10} 列\n"

        context += f"""
## 数据质量
- 完整度：{quality["completeness"]}%
- 重复行：{quality["duplicate_rows"]}
- 异常值：{quality["outliers_count"]}
- 质量评分：{quality["quality_score"]}/100 ({quality["quality_level"]})

## 推荐分析策略
- 策略类型：{strategy["type"]}
- {strategy["description"]}
- 最大展示系列数：{strategy["max_series"]}
- 推荐图表：{", ".join(strategy["recommended_charts"])}

## 重要提示
1. 使用下面的列名时，必须完全匹配（包括大小写和空格）
2. 如果表格是宽表，第一列是指标名，需要转置处理
3. 数据量较大时，请使用聚合或抽样，不要尝试渲染所有数据
4. 检测到的数值列：{", ".join([c["name"] for c in structure["columns"] if c["is_numeric"]][:5])}
"""
        return context

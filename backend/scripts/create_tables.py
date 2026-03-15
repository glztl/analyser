"""
数据库表初始化脚本
用于在开发/部署时创建所有表结构

使用方式:
    cd backend
    uv run python scripts/create_tables.py
"""

import asyncio
import sys
from pathlib import Path

# ✅ 关键：将项目根目录加入路径，确保能导入 app 模块
# 这样脚本无论从哪个目录运行都能找到模块
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.database import engine, Base
# ✅ 必须导入所有模型模块，否则它们的元数据不会注册到 Base.metadata
from app.models import task  # 导入 task 模型


async def create_tables():
    """
    异步创建所有数据库表
    """
    print("🔄 正在连接数据库...")
    
    try:
        # 使用 engine.begin() 开启一个事务上下文
        async with engine.begin() as conn:
            print("🔍 检查现有表结构...")
            
            # 查询当前数据库中已存在的表
            result = await conn.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
            )
            existing_tables = [row[0] for row in result.fetchall()]
            print(f"📋 当前数据库已有表: {existing_tables or '无'}")
            
            # ✅ 创建所有未在数据库中存在的表
            # Base.metadata.create_all 会自动跳过已存在的表（如果支持 IF NOT EXISTS）
            # 但 asyncpg + PostgreSQL 需要显式处理，所以我们用 sync 方式在 run_sync 中执行
            await conn.run_sync(Base.metadata.create_all)
            
            print("✅ 表结构创建/更新成功！")
            
            # 验证关键表是否创建成功
            result = await conn.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'analysis_tasks'
                    );
                """)
            )
            if result.scalar():
                print("✅ 验证: analysis_tasks 表已就绪")
            else:
                print("⚠️  警告: analysis_tasks 表可能未正确创建")
                
    except Exception as e:
        print(f"❌ 创建表失败: {type(e).__name__}: {e}")
        # 打印更详细的错误信息，方便调试
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # ✅ 关键：关闭引擎，释放连接池资源
        await engine.dispose()
        print("🔌 数据库连接已关闭")
    
    return True


async def drop_tables():
    """
    [危险操作] 删除所有表
    仅用于开发环境重置数据库
    """
    print("⚠️  警告: 即将删除所有表结构！")
    confirm = input("确认要删除所有表吗？输入 'yes' 继续: ")
    
    if confirm.strip().lower() != 'yes':
        print("🚫 操作已取消")
        return
    
    try:
        async with engine.begin() as conn:
            # 使用 CASCADE 级联删除（注意：会删除外键关联的数据）
            await conn.run_sync(Base.metadata.drop_all)
        print("✅ 所有表已删除")
    except Exception as e:
        print(f"❌ 删除失败: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库表管理脚本")
    parser.add_argument(
        "--drop", 
        action="store_true", 
        help="删除所有表（危险操作，仅开发环境使用）"
    )
    args = parser.parse_args()
    
    print(f"🚀 Analyser 数据库初始化脚本 (环境: {'开发' if '--drop' in sys.argv else '生产'})")
    print("-" * 60)
    
    if args.drop:
        # 执行删除操作
        asyncio.run(drop_tables())
    else:
        # 执行创建操作（默认）
        success = asyncio.run(create_tables())
        # 根据结果设置退出码，便于 CI/CD 判断
        sys.exit(0 if success else 1)
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def test_connection():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ 数据库连接成功！PostgreSQL 版本: {version}")
            
            # 测试表是否存在
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'analysis_tasks'
                );
            """))
            exists = result.scalar()
            if exists:
                print("✅ 表 analysis_tasks 已存在")
            else:
                print("⚠️  表 analysis_tasks 不存在，需要运行创建脚本")
    except Exception as e:
        print(f"❌ 连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
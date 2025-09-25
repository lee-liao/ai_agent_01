import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def verify_db_from_database_py():
    """Verify the database connection using the same logic as database.py."""
    try:
        print("Attempting to create SQLAlchemy async engine...")
        engine = create_async_engine(
            "postgresql+asyncpg://rag_user:rag_password_2024@localhost:5433/rag_chatbot",
            #"postgres+asyncpg://rag_user:rag_password_2024@localhost:5433/rag_chatbot",
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            echo=True,
            future=True,
        )
        print("Success: SQLAlchemy async engine created successfully.")

        print("\nAttempting to connect to the database...")
        async with engine.connect() as connection:
            print("Success: Database connection successful!")
            result = await connection.execute(text("SELECT 1"))
            print(f"Success: Test query successful, result: {result.scalar()}")

    except Exception as e:
        print(f"Error: An error occurred: {e}")
    finally:
        if 'engine' in locals() and engine:
            await engine.dispose()
            print("\nEngine disposed.")

if __name__ == "__main__":
    asyncio.run(verify_db_from_database_py())
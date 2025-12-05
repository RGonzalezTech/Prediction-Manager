from sqlalchemy import inspect
from sqlalchemy.engine import reflection
from app.database.database import engine, SessionLocal
from app.models.models import Base, User, Category

async def init_db():
    async with engine.begin() as conn:
        
        # Run synchronous inspection and potential ALTER
        def run_migration_if_needed(conn):
            inspector = inspect(conn)
            if "predictions" in inspector.get_table_names():
                columns = [c["name"] for c in inspector.get_columns("predictions")]
                if "opponent_id" not in columns:
                    conn.exec_driver_sql(
                        "ALTER TABLE predictions ADD COLUMN opponent_id INTEGER REFERENCES users(id)"
                    )

        await conn.run_sync(run_migration_if_needed)
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        if (await session.execute(User.__table__.select())).first() is None:
            session.add_all(
                [
                    User(name="Husband"),
                    User(name="Wife"),
                ]
            )
            await session.commit()

        if (await session.execute(Category.__table__.select())).first() is None:
            session.add_all(
                [
                    Category(name="Love is Blind"),
                    Category(name="General"),
                    Category(name="Politics"),
                ]
            )
            await session.commit()

from alembic import context
from sqlalchemy import create_engine
from app.config import get_settings
from app.database.models import Base

engine = create_engine(get_settings().database_url.get_secret_value())
with engine.connect() as connection:
    # Serializes concurrent migration invocations without exposing readiness early.
    connection.exec_driver_sql("SELECT pg_advisory_lock(170101)")
    connection.commit()
    try:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.exec_driver_sql("SELECT pg_advisory_unlock(170101)")
        connection.commit()

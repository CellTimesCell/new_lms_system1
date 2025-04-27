# scripts/initialize_database.py
import sys
import os
import logging
from sqlalchemy_utils import database_exists, create_database

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import database config
from infrastructure.databases.database_config import engine, SQLALCHEMY_DATABASE_URL
from infrastructure.databases.database_config import get_clickhouse_client
from alembic.config import Config
from alembic import command

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_postgres():
    """Initialize PostgreSQL database"""
    try:
        # Create database if it doesn't exist
        if not database_exists(SQLALCHEMY_DATABASE_URL):
            create_database(SQLALCHEMY_DATABASE_URL)
            logger.info(f"Created database: {SQLALCHEMY_DATABASE_URL}")
        else:
            logger.info(f"Database already exists: {SQLALCHEMY_DATABASE_URL}")

        # Run Alembic migrations
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Successfully applied Alembic migrations")

        return True
    except Exception as e:
        logger.error(f"Error initializing PostgreSQL: {str(e)}")
        return False


def init_clickhouse():
    """Initialize ClickHouse database"""
    try:
        # Get ClickHouse client
        ch_client = get_clickhouse_client()

        # Run initialization SQL
        with open("infrastructure/databases/clickhouse_init.sql", "r") as f:
            sql = f.read()

        # Split and execute statements
        for statement in sql.split(';'):
            if statement.strip():
                ch_client.execute(statement)

        logger.info("Successfully initialized ClickHouse database")
        return True
    except Exception as e:
        logger.error(f"Error initializing ClickHouse: {str(e)}")
        return False


def main():
    """Main initialization function"""
    logger.info("Starting database initialization...")

    # Initialize PostgreSQL
    pg_success = init_postgres()

    # Initialize ClickHouse
    ch_success = init_clickhouse()

    if pg_success and ch_success:
        logger.info("Database initialization completed successfully!")
    else:
        logger.error("Database initialization encountered errors")


if __name__ == "__main__":
    main()
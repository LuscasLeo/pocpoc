import logging
from io import StringIO
from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Engine

from pocpoc.api.microservices import Container

logger = logging.getLogger(__name__)


class CheckDatabaseMigration:
    def __init__(self, engine: Engine, db_version_path: Path) -> None:
        self.engine = engine
        self.db_version_path = db_version_path

    def __call__(self, container: Container) -> None:
        connection = self.engine.connect()
        with connection:
            output_buffer = StringIO()
            context = MigrationContext.configure(
                connection, opts={"output_buffer": output_buffer}
            )
            db_current_revision = context.get_current_revision()

            config = config = Config(str(self.db_version_path / "alembic.ini"))
            config.set_main_option("script_location", str(self.db_version_path))
            config.config_file_name = None
            script = ScriptDirectory.from_config(config)

            repository_current_revision = script.get_current_head()

            if db_current_revision != repository_current_revision:

                def on_revision_apply(
                    context: EnvironmentContext, revision: MigrationContext, **kw: Any
                ) -> None:
                    return script._upgrade_revs("head", db_current_revision)  # type: ignore

                env = EnvironmentContext(
                    config,
                    script,
                    fn=on_revision_apply,
                    starting_rev=db_current_revision,
                    as_sql=True,
                )
                env.configure(
                    output_buffer=output_buffer,
                    dialect=context.dialect,
                    dialect_opts=context.opts,
                    connection=context.connection,
                )
                with env:
                    script.run_env()

                sql = output_buffer.getvalue()

                logger.warning(
                    "Database is not up to date. Current revision on database: %s. Current revision on repository: %s. May the microservice does not perform as well. run the following SQL to update the database: \n\n %s",
                    db_current_revision,
                    repository_current_revision,
                    sql,
                )

                with open("migration.sql", "w") as f:
                    f.write(sql)

                logger.warning("SQL migration script saved to migration.sql")

            connection.close()


class CheckDatabaseConnection:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def __call__(self, container: Container) -> None:
        try:
            connection = self.engine.connect()
            connection.execute("SELECT 1")  # type: ignore
        except Exception as e:
            logger.fatal("Error connecting to database: %s", e)
            raise e

        connection.close()
        logger.debug("Database connection OK")

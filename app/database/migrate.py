from os import listdir, path

from aiomysql import Pool

from definitions import ROOT_DIR, LOGGER


async def migrate(database_pool: Pool):
    async with database_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('''
                SELECT TABLE_NAME
                FROM information_schema.TABLES 
                WHERE TABLE_TYPE LIKE 'BASE TABLE' 
                    AND TABLE_SCHEMA = 'main' 
                    AND TABLE_NAME = 'migrations'
            ''')
            if (await cursor.fetchone()) is None:
                await cursor.execute('CREATE TABLE migrations (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY)')
            migration_files = sorted(listdir(path.join(ROOT_DIR, 'app', 'database', 'versions')))
            await cursor.execute('SELECT id FROM migrations')
            applied_versions = [str(version[0]) for version in await cursor.fetchall()]
            for file_name in migration_files:
                version = file_name.split('_')[0]
                if file_name.endswith('migration.py') and \
                        version not in applied_versions:
                    migration = __import__(f'app.database.versions.{file_name[:-3]}',
                                           fromlist=['upgrade'])
                    await migration.upgrade(conn)
                    await cursor.execute('INSERT INTO migrations (id) VALUES (%s)', (version,))
                    await conn.commit()
                    LOGGER.info(f'migration v{version} applied')

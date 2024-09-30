from aiomysql import Connection


async def upgrade(conn: Connection):
    async with conn.cursor() as cursor:
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(255) NOT NULL,
                description TEXT NULL,
                location VARCHAR(255) NULL
            )
        ''')
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS periods_metadata (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                start DATE NOT NULL,
                end DATE NOT NULL,
                summary VARCHAR(255) NOT NULL
            );
        ''')
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS weeks (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                start DATE NOT NULL,
                end DATE NOT NULL
            );
        ''')
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                subject_id INT UNSIGNED NOT NULL,
                serial_number INT UNSIGNED NOT NULL,
                start TIMESTAMP NOT NULL,
                end TIMESTAMP NOT NULL,
                odd_week BOOLEAN NOT NULL,
                repeat_until TIMESTAMP NOT NULL
            )
        ''')
        await conn.commit()

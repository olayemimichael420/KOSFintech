import sqlite3


def test_sqlite_foreign_keys_are_enforced():
    connection = sqlite3.connect(":memory:")

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute(
            """
            CREATE TABLE roles (
                id INTEGER PRIMARY KEY
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE user_roles (
                role_id INTEGER NOT NULL,
                FOREIGN KEY (role_id) REFERENCES roles(id)
            )
            """
        )

        try:
            connection.execute(
                "INSERT INTO user_roles (role_id) VALUES (?)",
                (999999,),
            )
            connection.commit()
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError(
                "Foreign-key constraint was not enforced"
            )

    finally:
        connection.close()

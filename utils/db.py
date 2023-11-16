# WILL USE AN ORM INSTEAD
import sqlite3
from sqlite3 import Error


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    finally:
        if conn:
            return conn


# SETUP DB
def clear_db():
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("DROP TABLE IF EXISTS organizations")
        cursor.execute("DROP TABLE IF EXISTS files")
        cursor.execute("DROP TABLE IF EXISTS short_codes")
        cursor.execute("DROP TABLE IF EXISTS short_code_files")
        cursor.execute("DROP TABLE IF EXISTS messages")
        conn.commit()
        print(f"DB cleared successfully")
    except Error as e:
        print(e)

    conn.commit()
    conn.close()


def init_db():
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Clear and create the organizations table
    clear_db()
    try:
        cursor.execute(
            """CREATE TABLE organizations
            (id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            address TEXT NOT NULL,
            description TEXT NOT NULL)"""
        )
        cursor.execute(
            """CREATE TABLE files
            (id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            organization_id INTEGER NOT NULL,
            weaviate_class TEXT NOT NULL UNIQUE,
            UNIQUE (name, organization_id),
            FOREIGN KEY (organization_id) REFERENCES organizations(id))"""
        )
        cursor.execute(
            """CREATE TABLE short_codes
            (id INTEGER PRIMARY KEY,
            short_code TEXT NOT NULL UNIQUE,
            organization_id INTEGER NOT NULL,
            UNIQUE (short_code, organization_id),
            FOREIGN KEY (organization_id) REFERENCES organizations(id))"""
        )
        cursor.execute(
            """CREATE TABLE short_code_files
            (id INTEGER PRIMARY KEY,
            short_code_id TEXT NOT NULL,
            file_id INTEGER NOT NULL,
            UNIQUE (short_code_id, file_id),
            FOREIGN KEY (file_id) REFERENCES files(id),
            FOREIGN KEY (short_code_id) REFERENCES short_codes(id))"""
        )
        cursor.execute(
            """CREATE TABLE messages
            (id INTEGER PRIMARY KEY,
            content TEXT NOT NULL,
            shortcode_id INT NOT NULL,
            organization_id INT NOT NULL,
            FOREIGN KEY (organization_id) REFERENCES organizations(id))"""
        )
        conn.commit()
        print(f"DB initialized successfully")
    except Error as e:
        print(e)

    conn.commit()
    conn.close()


def insert_dummy_data():
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        # Organizations
        cursor.execute(
            "INSERT INTO organizations (name, address, description, email,password) VALUES (?, ?, ?, ?, ?)",
            (
                "WHO",
                "123 Main St.",
                "We champion health and a better future for all. Dedicated to the well-being of all people and guided by science, the World Health Organization leads and champions global efforts to give everyone, everywhere an equal chance to live a healthy life.",
                "info@acme.com",
                "passowrd",
            ),
        )
        cursor.execute(
            "INSERT INTO organizations (name, address, description, email, password) VALUES (?, ?, ?, ?, ?)",
            (
                "Globex Corp",
                "456 Elm St.",
                "An imaginary company",
                "info@globex.com",
                "passowrd",
            ),
        )

        # Files
        # cursor.execute(
        #     "INSERT INTO files (name, description, organization_id, weaviate_class) VALUES (?, ?, ?, ?)",
        #     (
        #         "pragnancy_book.pdf",
        #         "Improving maternal health awareness",
        #         1,
        #         "WHO_pragnancy_book",
        #     ),
        # )
        # cursor.execute(
        #     "INSERT INTO files (name, description, organization_id, weaviate_class) VALUES (?, ?, ?, ?)",
        #     (
        #         "malaria.pdf",
        #         "Improving malaria disease awareness",
        #         1,
        #         "WHO_malaria",
        #     ),
        # )
        # cursor.execute(
        #     "INSERT INTO files (name, description, organization_id, weaviate_class) VALUES (?, ?, ?, ?)",
        #     ("Globex.pdf", "customer care chatbot file", 2, "GlobexCorp_Globex"),
        # )

        # Short Codes
        # cursor.execute(
        #     "INSERT INTO short_codes (short_code,organization_id) VALUES (?,?)",
        #     ("212", 1),
        # )
        # cursor.execute(
        #     "INSERT INTO short_codes (short_code, organization_id) VALUES (?,?)",
        #     ("309", 1),
        # )

        # Files Short Codes
        # cursor.execute(
        #     "INSERT INTO short_code_files (short_code_id,file_id) VALUES (?,?)",
        #     (1, 1),
        # )
        # cursor.execute(
        #     "INSERT INTO short_code_files (short_code_id,file_id) VALUES (?,?)",
        #     (2, 2),
        # )
        conn.commit()
        print(f"DB Populated successfully")
    except Error as e:
        print(e)

    conn.commit()
    conn.close()


def run_query(query):
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    results = []
    try:
        cursor.execute(query)
        results = cursor.fetchall()
    except Error as e:
        print(e)

    conn.commit()
    conn.close()
    return results


# ORGANIZATIONS
def add_organization(organization):
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO organizations (name, email, password, address, description) VALUES (?, ?, ?, ?, ?)",
            (
                organization.name,
                organization.email,
                organization.password,
                organization.address,
                organization.description,
            ),
        )
        last_row_id = cursor.lastrowid
    except Error as e:
        print(e)

    cursor.execute("SELECT * FROM organizations WHERE id = ?", (last_row_id,))
    row = cursor.fetchone()

    conn.commit()
    conn.close()
    return row


def get_organizations():
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM organizations")
        conn.commit()
    except Error as e:
        print(e)
    results = cursor.fetchall()
    conn.close()
    return results


# SHORT CODES
def add_short_code(shortcode):
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO short_codes (short_code, organization_id) VALUES (?, ?)",
            (shortcode["shortcode"], shortcode["organization_id"]),
        )
    except Error as e:
        print(e)

    last_row_id = cursor.lastrowid
    cursor.execute("SELECT * FROM short_codes WHERE id = ?", (last_row_id,))
    row = cursor.fetchone()

    conn.commit()
    conn.close()
    return row


def get_short_codes():
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM short_codes")
        conn.commit()
    except Error as e:
        print(e)
    results = cursor.fetchall()
    conn.close()
    return results


def get_short_code(shortcode):
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM short_codes JOIN files ON short_codes.organization_id = files.organization_id WHERE short_code = ?",
            (shortcode,),
        )
        conn.commit()
    except Error as e:
        print(e)
    result = cursor.fetchone()
    conn.close()
    return result


def delete_short_code(id):
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM short_codes WHERE id = ? RETURNING *", (id))
        row = cursor.fetchone()
    except Error as e:
        print(e)

    conn.commit()
    conn.close()
    return row


# FILES
def add_file(file):
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id FROM organizations WHERE name = ?", (file["organization"],)
        )
        found_organization = cursor.fetchone()
        cursor.execute(
            "INSERT INTO files (name, organization_id, description, weaviate_class) VALUES (?, ?, ?, ?)",
            (
                file["name"],
                found_organization["id"],
                file["description"],
                file["weaviate_class"],
            ),
        )
        last_row_id = cursor.lastrowid
        cursor.execute("SELECT * FROM files WHERE id = ?", (last_row_id,))
    except Error as e:
        print(e)
    row = cursor.fetchone()

    conn.commit()
    conn.close()
    return row


def add_file_to_short_code(short_code, file_id):
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        found_short_code = cursor.execute(
            "SELECT id FROM short_codes WHERE short_code=?", (short_code,)
        ).fetchone()
        if not found_short_code:
            cursor.execute(
                "INSERT INTO short_code_files (short_code_id, file_id) VALUES (?, ?)",
                (short_code, file_id),
            )
            conn.commit()
            last_row_id = cursor.lastrowid
            cursor.execute(
                "SELECT * FROM short_code_files WHERE id = ?", (last_row_id,)
            )
    except Error as e:
        print(e)
    row = cursor.fetchone()
    conn.close()
    return row


def add_message(message, organization_id, shortcode_id):
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO messages (content, organization_id, shortcode_id) VALUES (?, ?, ?)",
            (message, organization_id, shortcode_id),
        )
        conn.commit()
        last_row_id = cursor.lastrowid
        cursor.execute("SELECT * FROM messages WHERE id = ?", (last_row_id,))
    except Error as e:
        print(e)
    row = cursor.fetchone()
    conn.close()
    return row

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
        cursor.executescript(
            """
        DROP TABLE IF EXISTS organizations;
        DROP TABLE IF EXISTS files;
        DROP TABLE IF EXISTS short_codes;
        DROP TABLE IF EXISTS short_code_files;
        DROP TABLE IF EXISTS messages;
        DROP TABLE IF EXISTS areas;"""
        )
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
        cursor.executescript(
            """CREATE TABLE organizations
            (id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            address TEXT NOT NULL,
            description TEXT NOT NULL);
            
            CREATE TABLE files
            (id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            organization_id INTEGER NOT NULL,
            weaviate_class TEXT NOT NULL UNIQUE,
            UNIQUE (name, organization_id),
            FOREIGN KEY (organization_id) REFERENCES organizations(id));
            
            CREATE TABLE short_codes
            (id INTEGER PRIMARY KEY,
            short_code TEXT NOT NULL UNIQUE,
            organization_id INTEGER NOT NULL,
            UNIQUE (short_code, organization_id),
            FOREIGN KEY (organization_id) REFERENCES organizations(id));
            
            CREATE TABLE short_code_files
            (id INTEGER PRIMARY KEY,
            short_code_id TEXT NOT NULL,
            file_id INTEGER NOT NULL,
            UNIQUE (short_code_id, file_id),
            FOREIGN KEY (file_id) REFERENCES files(id),
            FOREIGN KEY (short_code_id) REFERENCES short_codes(id));
            
            CREATE TABLE messages
            (id INTEGER PRIMARY KEY,
            content TEXT NOT NULL,
            shortcode_id INT NOT NULL,
            organization_id INT NOT NULL,
            areas TEXT NOT NULL,
            FOREIGN KEY (organization_id) REFERENCES organizations(id));
            
            CREATE TABLE areas
            (id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            numbers TEXT NOT NULL);"""
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
        cursor.executescript(
            """INSERT INTO organizations (name, address, description, email,password) VALUES 
            (
                'WHO',
                '123 Main St.',
                'We champion health and a better future for all. Dedicated to the well-being of all people and guided by science, the World Health Organization leads and champions global efforts to give everyone, everywhere an equal chance to live a healthy life.',
                'info@who.com',
                'password'),
            (
                'Globex Corp',
                '456 Elm St.',
                'An imaginary company',
                'info@globex.com',
                'passowrd');
            """
        )
        cursor.executescript(
            """INSERT INTO short_codes (short_code,organization_id) VALUES 
            ("3525", 1);
            INSERT INTO files (name, description, organization_id, weaviate_class) VALUES 
            ("Pregnancy_Book_comp.pdf", "", 1, "WHO_Pregnancy_Book_comp");
            INSERT INTO short_code_files (short_code_id, file_id) VALUES 
            (1,1);
            """,
        )
        cursor.executescript(
            """
            INSERT INTO areas (name, numbers) VALUES 
            ('zaria - Kaduna state','+2347035251445,+2348012378000,+2347087654321'),
            ('igabi - Kaduna state','+2347035251445,+2348012345111,+2347087654321'),
            ('makarfi - Kaduna state','+23407035251445,+23408012345777,+2347087654321');
            """
        )
        conn.commit()
        print(f"DB Populated successfully")
    except Error as e:
        print(e)

    conn.commit()
    conn.close()


# ORGANIZATIONS
def add_organization(organization):
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    error = None
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
        conn.commit()
    except Error as e:
        print(e)
        error = e

    last_row_id = cursor.lastrowid
    if last_row_id:
        cursor.execute("SELECT * FROM organizations WHERE id = ?", (last_row_id,))
        row = cursor.fetchone()
        print(f'{row["name"]}')
        conn.close()
        return row
    else:
        conn.close()
        return {"error": error}


def get_organization(email: str):
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM organizations WHERE email = ?", (email,))
        conn.commit()
    except Error as e:
        print(e)
    result = cursor.fetchone()
    print(f'{result["name"]}')
    conn.close()
    return result


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
    print(row["short_code"])

    conn.commit()
    conn.close()
    return row


def get_short_codes(organization):
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM short_codes JOIN organizations ON short_codes.organization_id = organizations.id WHERE organizations.name = ?",
            (organization,),
        )
        conn.commit()
    except Error as e:
        print(e)
    results = cursor.fetchall()
    print(f'{row["name"]}')
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
    print(f'{result["short_code"]}')
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
    print(f"Added file {row['name']}")

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
            print(f'{found_short_code["name"]}')
    except Error as e:
        print(e)
    row = cursor.fetchone()
    conn.close()
    return row


def add_message(message, organization, shortcode, areas):
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM short_codes JOIN organizations ON short_codes.short_code = ?",
            (shortcode,),
        )
        found_shortcode = cursor.fetchone()
        cursor.execute(
            "INSERT INTO messages (content, organization_id, shortcode_id, areas) VALUES (?, ?, ?, ?)",
            (
                message,
                found_shortcode["organization_id"],
                found_shortcode["id"],
                "|".join(areas),
            ),
        )
        conn.commit()
        last_row_id = cursor.lastrowid
        print(f"message: {message}")
        cursor.execute(
            """
            SELECT *
            FROM messages m
            JOIN areas a ON m.areas LIKE '%' || a.name || '%'
            WHERE m.id = ?""",
            (last_row_id,),
        )

    except Error as e:
        print(e)
    row = cursor.fetchall()
    conn.close()
    return row


def get_messages(organization):
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM messages JOIN organizations ON messages.organization_id = organizations.id JOIN short_codes ON shortcode_id = short_codes.id WHERE organizations.name = ?",
            (organization,),
        )
    except Error as e:
        print(e)
    rows = cursor.fetchall()
    print(rows)
    conn.close()
    return rows


def get_areas():
    conn = create_connection(r"db\connected.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM areas")
    except Error as e:
        print(e)
    rows = cursor.fetchall()
    print(rows)
    conn.close()
    return rows

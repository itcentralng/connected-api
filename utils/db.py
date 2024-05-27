# using postgreSQL

from fastapi import HTTPException
from psycopg2 import Error
from werkzeug.security import generate_password_hash
import os
import psycopg2.extras


def create_connection():
    conn = None
    try:
        user = os.environ.get("DB_USERNAME")
        password = os.environ.get("DB_PASSWORD")
        host = os.environ.get("DB_HOST")
        port = os.environ.get("DB_PORT")
        conn = psycopg2.connect(
            user=user, password=password, host=host, port=port, database="postgres",
            cursor_factory=psycopg2.extras.RealDictCursor,  # Return rows as dictionaries

        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))



# SETUP DB
def clear_db():
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
        DROP TABLE IF EXISTS organizations CASCADE;
        DROP TABLE IF EXISTS files CASCADE;
        DROP TABLE IF EXISTS short_codes CASCADE;
        DROP TABLE IF EXISTS short_code_files CASCADE;
        DROP TABLE IF EXISTS messages CASCADE;
        DROP TABLE IF EXISTS areas CASCADE;"""
        )
        conn.commit()
        print(f"DB cleared successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))

    conn.commit()
    conn.close()


def init_db():
    conn = create_connection()
    cursor = conn.cursor()
    # Clear and create the organizations table
    clear_db()
    try:
        cursor.execute(
            """CREATE TABLE organizations
            (id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            address TEXT NOT NULL,
            description TEXT NOT NULL);
            
            CREATE TABLE files
            (id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            organization_id INTEGER NOT NULL,
            weaviate_class TEXT NOT NULL UNIQUE,
            UNIQUE (name, organization_id),
            FOREIGN KEY (organization_id) REFERENCES organizations(id));
            
            CREATE TABLE short_codes
            (id SERIAL PRIMARY KEY,
            short_code TEXT NOT NULL UNIQUE,
            organization_id INTEGER NOT NULL,
            UNIQUE (short_code, organization_id),
            FOREIGN KEY (organization_id) REFERENCES organizations(id));
            
            CREATE TABLE short_code_files
            (id SERIAL PRIMARY KEY,
            short_code_id INTEGER NOT NULL,
            file_id SERIAL NOT NULL,
            UNIQUE (short_code_id, file_id),
            FOREIGN KEY (file_id) REFERENCES files(id),
            FOREIGN KEY (short_code_id) REFERENCES short_codes(id));
            
            CREATE TABLE messages
            (id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            shortcode_id INT NOT NULL,
            organization_id INTEGER NOT NULL,
            areas TEXT NOT NULL,
            FOREIGN KEY (organization_id) REFERENCES organizations(id));
            
            CREATE TABLE areas
            (id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            numbers TEXT NOT NULL);"""
        )
        conn.commit()
        print(f"DB initialized successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))

    conn.close()


def insert_dummy_data():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO areas (name, numbers) VALUES 
            ('zaria - Kaduna state','+2348162577778');
            """
        )
        conn.commit()
        print(f"DB Populated successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))

    conn.close()


# ORGANIZATIONS
def add_organization(organization):
    conn = create_connection()
    cursor = conn.cursor()
    error = None
    try:
        hashed_password = generate_password_hash(organization.password)
        cursor.execute(
            "INSERT INTO organizations (name, email, password, address, description) VALUES (%s, %s, %s, %s, %s)",
            (
                organization.name,
                organization.email,
                hashed_password,
                organization.address,
                organization.description,
            ),
        )
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))

    last_row_id = cursor.lastrowid
    if last_row_id:
        cursor.execute("SELECT * FROM organizations WHERE id = %s", (last_row_id,))
        row = cursor.fetchone()
        conn.close()
        return row
    else:
        conn.close()
        return {"error": error}


def get_organization(email: str):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM organizations WHERE email = %s", (email,))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        if isinstance(result, tuple):
            organization_dict = {
                "id": result[0],
                "name": result[1],
                "email": result[2],
                "password": result[3],
                "address": result[4],
                "description": result[5]
            }
            return organization_dict
        elif isinstance(result, dict):  # Assuming you're using RealDictRow
            return result
    else:
        return None
        


# SHORT CODES
def add_short_code(shortcode, organization_id):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO short_codes (short_code, organization_id) VALUES (%s, %s)",
            (shortcode, organization_id),
        )

        conn.commit()
        conn.close()
        return True
    except Error as e:
        print(e)
        conn.rollback()
        return False



def get_short_codes(organization):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM short_codes JOIN organizations ON short_codes.organization_id = organizations.id WHERE organizations.name ilike %s",
            (organization,),
        )
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))
    results = cursor.fetchall()
    conn.close()
    return results


def get_short_code(shortcode):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT *
            FROM short_code_files as scf
            JOIN short_codes as sc ON scf.short_code_id = sc.id
            JOIN files as f ON scf.file_id = f.id
            WHERE sc.short_code = %s;
            """,
            (shortcode,),
        )
        result = cursor.fetchone()
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))
    conn.close()
    return result


def delete_short_code(id):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM short_codes WHERE id = %s RETURNING *", (id))
        row = cursor.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))

    conn.commit()
    conn.close()
    return row


# FILES
def add_file(file):
    conn = create_connection()
    # conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id FROM organizations WHERE name ilike %s", (file["organization"],)
        )
        found_organization = cursor.fetchone()
        cursor.execute(
            "INSERT INTO files (name, organization_id, weaviate_class) VALUES (%s, %s, %s)",
            (
                file["name"],
                found_organization["id"],
                file["weaviate_class"],
            ),
        )
        last_row_id = cursor.lastrowid
        cursor.execute("SELECT * FROM files WHERE id = %s", (last_row_id,))
        status = True
    except Error as e:
        print(e)
        status = False
    

    conn.commit()
    conn.close()
    return status



def add_file_to_short_code(short_code, file_id):
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id FROM short_codes WHERE short_code=%s", (short_code,)
        )
        found_short_code = cursor.fetchone()
        # if found_short_code:
        #     print('Found', short_code)
        # else:
        #     print('not found ', short_code)
        cursor.execute(
            "SELECT id FROM files WHERE name=%s", (file_id,)
        )
        found_file = cursor.fetchone()
        if found_short_code and found_file:
            cursor.execute(
                "INSERT INTO short_code_files (short_code_id, file_id) VALUES (%s, %s)",
                (found_short_code['id'], found_file['id']),  # Use found_short_code["id"] as short_code_id and found_file["id"] as file_id
            )
            conn.commit()
            last_row_id = cursor.lastrowid
            cursor.execute(
                "SELECT * FROM short_code_files WHERE id = %s", (last_row_id,)
            )
            row = cursor.fetchone()  
    except Error as e:
        print(e)
        row = None  # Set row to None if an error occurs
    conn.close()
    return row




def add_message(message, organization, shortcode, areas):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM short_codes WHERE short_code = %s",
            (shortcode,),
        )
        found_shortcode = cursor.fetchone()
        cursor.execute(
            "INSERT INTO messages (content, organization_id, shortcode_id, areas) VALUES (%s, %s, %s, %s)",
            (
                message,
                found_shortcode["organization_id"],
                found_shortcode["id"],
                "|".join(areas),
            ),
        )
        conn.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))
    conn.close()


def get_messages(organization):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM messages JOIN organizations ON messages.organization_id = organizations.id JOIN short_codes ON shortcode_id = short_codes.id WHERE organizations.name = %s",
            (organization,),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_areas():
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM areas")
    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_files(organization_id):
    conn = create_connection()
    cursor = conn.cursor()
    try:

        cursor.execute(
            """
            SELECT sc.short_code, f.name
            FROM short_codes sc
            JOIN short_code_files scf ON sc.id = scf.short_code_id
            JOIN files f ON f.id = scf.file_id
            WHERE sc.organization_id = %s
            """,
        (organization_id,))
        joined_data = cursor.fetchall()
    except Error as e:
        print(e)
    conn.close()
    return joined_data



def insert_new_number(area_name, numbers):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE areas SET numbers = CONCAT(numbers, ',', %s) WHERE name = %s;
            """,
            (numbers, area_name)
        )
        conn.commit()
        print(f"Numbers added successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))

    conn.commit()
    conn.close()


def get_phone_numbers():
    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT numbers FROM areas")
        results = cursor.fetchall()
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

    conn.close()

    # Extract and flatten the phone numbers from the results
    phone_numbers = []
    for row in results:
        numbers = row['numbers'].split(", ")
        cleaned_numbers = [number.strip() for number in numbers]
        phone_numbers.extend(cleaned_numbers)

    return phone_numbers


def add_area(name: str, numbers: str) -> bool:
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO areas (name, numbers) VALUES (%s, %s);
            """,
            (name, numbers)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        print(e)
        return False

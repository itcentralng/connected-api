import os
from supabase import create_client, Client
from dotenv import load_dotenv
from postgrest.exceptions import APIError
import bcrypt
import base64


load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

    return base64.b64encode(hashed_password).decode("utf-8")


def verify_password(db_password, password):
    return bcrypt.checkpw(
        password.encode("utf-8"), base64.b64decode(db_password.encode("utf-8"))
    )


def add_organization(organization):
    organization.password = hash_password(organization.password)
    try:
        response = (
            supabase.table("_organizations").insert(organization.__dict__).execute()
        )
        return response
    except Exception as error:
        return {"error": error}


def get_organization(organization):
    try:
        response = (
            supabase.table("_organizations")
            .select("*")
            .eq("email", organization.email)
            .single()
            .execute()
        )
    except Exception as error:
        return {"error": error}

    if response.data:
        db_password = response.data["password"]

        if verify_password(db_password, organization.password):
            del response.data["password"]
            return response
        else:
            return {"error": "Invalid credentials"}
    else:
        return {"error": "Invalid credentials"}


def add_file(organization, file):
    try:
        organization_from_db = (
            supabase.table("_organizations")
            .select("id")
            .eq("name", organization)
            .single()
            .execute()
        )
        response = (
            supabase.table("files")
            .insert(
                {
                    "name": file["filename"],
                    "organization_id": organization_from_db.data["id"],
                    "description": file["description"],
                    "weaviate_class": file["weaviate_class"],
                }
            )
            .execute()
        )
        print(f"Added file -> {file['weaviate_class']}")
        return response
    except Exception as error:
        print(f"Error: {error}")
        return {"error": error}


def add_shortcode(organization, shortcode):
    try:
        organization_from_db = (
            supabase.table("_organizations")
            .select("id")
            .eq("name", organization)
            .single()
            .execute()
        )
        response = (
            supabase.table("shortcodes")
            .insert(
                {
                    "organization_id": organization_from_db.data["id"],
                    "shortcode": shortcode,
                }
            )
            .execute()
        )
        if response.data:
            print(f"Added shortcode -> {shortcode} for organization -> {organization}")
        return response
    except Exception as error:
        print(f"Error: {error}")
        return {"error": error}


def check_shortcode(shortcode):
    try:
        shortcode = (
            supabase.table("shortcodes")
            .select("id")
            .eq("shortcode", shortcode)
            .single()
            .execute()
        )
        if shortcode.data:
            print(f"Shortcode -> {shortcode} already exists")
        return shortcode
    except Exception as error:
        print(f"Error: {error}")
        return {"error": error}


def get_shortcodes(organization):
    try:
        organization_from_db = (
            supabase.table("_organizations")
            .select("*")
            .eq("name", organization)
            .single()
            .execute()
        )
        shortcodes = (
            supabase.table("shortcodes")
            .select("*")
            .eq("organization_id", organization_from_db.data["id"])
            .execute()
        )
        return shortcodes
    except Exception as error:
        print(f"Error: {error}")
        return {"error": error}


def get_shortcode(shortcode):
    try:
        shortcode = (
            supabase.table("shortcodes")
            .select("*")
            .eq("shortcode", shortcode)
            .single()
            .execute()
        )
        return shortcode
    except Exception as error:
        print(f"Error: {error}")
        return {"error": error}


def get_shortcode_files(shortcode):
    try:
        found_shortcode = (
            supabase.table("shortcodes")
            .select("*")
            .eq("shortcode", shortcode)
            .single()
            .execute()
        )
        shortcode = (
            supabase.table("files_shortcodes")
            .select("*, shortcodes(*), files(*)")
            .eq("shortcode_id", found_shortcode.data["id"])
            .single()
            .execute()
        )
        return shortcode
    except Exception as error:
        print(f"Error: {error}")
        return {"error": error}


def add_file_to_shortcode(shortcode_id, file_id):
    try:
        response = (
            supabase.table("files_shortcodes")
            .insert({"shortcode_id": shortcode_id, "file_id": file_id})
            .execute()
        )
        print(f"Added file with id -> {file_id} to shortcode id -> {shortcode_id}")
        return response
    except Exception as error:
        print(f"Error: {error}")
        return {"error": error}


def get_areas():
    try:
        areas = supabase.table("areas").select("*").execute()
        return areas
    except Exception as error:
        return {"error": error}


def get_message_areas(areas):
    try:
        areas = supabase.table("areas").select("*").in_("name", areas).execute()
        return areas.data
    except Exception as error:
        return {"error": error}


def add_message(message, organization, shortcode, areas):
    try:
        found_shortcode = (
            supabase.table("shortcodes")
            .select("id, _organizations(id)")
            .eq("_organizations.name", organization)
            .single()
            .execute()
        )
        added_message = (
            supabase.table("messages")
            .insert(
                {
                    "content": message,
                    "shortcode_id": found_shortcode.data["id"],
                    "organization_id": found_shortcode.data["_organizations"]["id"],
                    "areas": "|".join(areas),
                }
            )
            .execute()
        )
        return added_message
    except Exception as error:
        return {"error": error}


def get_messages(organization):
    try:
        messages = (
            supabase.table("messages")
            .select("*, _organizations(name), shortcodes(*)")
            .eq("_organizations.name", organization)
            .execute()
        )
        return messages
    except Exception as error:
        return {"error": error}


def get_files(organization):
    try:
        messages = (
            supabase.table("files_shortcodes")
            .select("*, files(*,_organizations(name)), shortcodes(*)")
            .eq("files._organizations.name", organization)
            .execute()
        )
        return messages
    except Exception as error:
        return {"error": error}

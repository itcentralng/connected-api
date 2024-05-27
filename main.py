from fastapi import FastAPI, File, HTTPException
from pydantic import BaseModel
from typing import Annotated
from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain.llms.cohere import Cohere
from langchain.document_loaders import PyPDFLoader
from dotenv import load_dotenv
import shutil
import weaviate
from langchain.vectorstores import Weaviate
from utils.weaviate import wv_upload_doc, wv_create_class
from utils.weaviate import ask_question
from utils import db
from utils.africastalking import AfricasTalking
import urllib.parse
from werkzeug.security import check_password_hash
import os

# initialize database on first run
# db.init_db()
# db.insert_dummy_data()

load_dotenv()
app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:5173",
    "*",
    "https://www.connectedai.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

wv_client = weaviate.Client(
    url=os.environ.get("WEAVIATE_URL"),
    auth_client_secret=weaviate.AuthApiKey(api_key=os.environ.get("WEAVIATE_API_KEY")),
    additional_headers={"X-Cohere-Api-Key": os.environ.get("COHERE_API_KEY")},
)

class LoginOrganization(BaseModel):
    email: str
    password: str

class Organization(BaseModel):
    name: str
    email: str
    password: str
    address: str
    description: str
    password: str

class ShortCode(BaseModel):
    short_code: int
    organization_id: int


class FileInfo(BaseModel):
    file_id: int

class Sms(BaseModel):
    shortcode: str

class Message(BaseModel):
    content: str
    shortcode: str
    areas: list


class AreaAndNumbers(BaseModel):
    area_name: str
    numbers: str
    
    
class Area(BaseModel):
    name: str
    numbers: str



@app.get("/")
def read_root():
    return {"app": "connected", "status": "ok"}


@app.post("/register")
def register_org(organization: Organization):
    try:
        added_organization = db.add_organization(organization)
        return added_organization
    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))


@app.post("/organization")
def login_organization(organization: LoginOrganization):
    result = db.get_organization(organization.email)
    try:
        if result and check_password_hash(result["password"], organization.password):
            return result
        raise HTTPException(status_code=401, detail="Wrong credentials entered")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/organization/{organization}/uploadfile")
async def create_upload_file(organization: str, file: UploadFile = Form(...), shortcode: str = Form(...), organization_id: str = Form(...)):
    
    wv_class_name = f"{organization}_{file.filename.split('.')[0]}".replace(
        " ", ""
    ).replace("-", "")
    classes = [row["class"].upper() for row in wv_client.schema.get()["classes"]]

    # DB Operations
    added_file = db.add_file(
        {
            "name": file.filename,
            "organization": organization,
            "weaviate_class": wv_class_name,
        }
    )
    if added_file:
        added_shortcode = db.add_short_code(shortcode, organization_id)
        if added_shortcode:
            db.add_file_to_short_code(shortcode, file.filename)

    if wv_class_name.upper() not in classes:
        wv_create_class(wv_client, wv_class_name)
        try:
            if not os.path.exists("uploads"):
                os.mkdir("uploads")

            with open(f"uploads/{file.filename}", "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            loader = PyPDFLoader(f"uploads/{file.filename}")
            doc = loader.load()
            wv_upload_doc(wv_client, doc, wv_class_name) #################

        except ValueError:
            return {"message": f"file: {file.filename} was not uploaded to server"}
        except AttributeError:
            return {"message": f"File: {file.filename} was not uploaded to weaviate"}
        finally:
            file.file.close()
    else:
        return {"msg": "File already exists"}
    # return added_file
    return {}

@app.post("organizations/{organization}/deletefile")
async def delete_files(organization: str, filename: str):
    wv_client.schema.delete_class()
    return {"message": f"{organization}_{filename.split('.')[0]}"}


@app.get("/{organization_id}/files")
async def get_short_codes(organization_id: int):
    results = db.get_files(organization_id)
    return results


@app.post("/{organization}/shortcode/add")
def register_short_code(short_code: ShortCode, organization: str):
    added_short_code = db.add_short_code(short_code)
    return {"shortcode": added_short_code}


@app.get("/{organization}/shortcodes")
async def get_short_codes(organization: str):
    results = db.get_short_codes(organization)
    return {"short_codes": results}


@app.get("/{organization}/shortcode/{id}/delete")
def register_short_code(id):
    removed_short_code = db.delete_short_code(id)
    return {"removed": removed_short_code}


@app.post("/sms")
async def receive_sms(request: Request):
    try:
        decoded_string = await request.body()
        parsed_dict = urllib.parse.parse_qs(decoded_string.decode("utf-8"))
        chat_history = []
        
        phone_numbers = db.get_phone_numbers()
        sender_number = parsed_dict["from"][0] 
        
        if sender_number not in phone_numbers:
            AfricasTalking().send(
                parsed_dict["to"][0],
                """Sorry, your number is not registered in our system. Kindly reach out to us at info@connectedai.net if you want your number to be registered on our system.""",
                [sender_number],
            )
            return {"message": "Number not registered"}
        
        result = db.get_short_code(parsed_dict["to"][0])
        if result and parsed_dict["text"][0]:
            vectorstore = Weaviate(wv_client, result["weaviate_class"], "content")
            answer = ask_question(
                vectorstore,
                Cohere(temperature=0), 
                parsed_dict["text"][0],
                chat_history,
            )
            classes = [row["class"].upper() for row in wv_client.schema.get()["classes"]]
            AfricasTalking().send(parsed_dict["to"][0], answer, [parsed_dict["from"][0]])
            return {"answer": answer}
        else:
            AfricasTalking().send(
                parsed_dict["to"][0],
                "Sorry we are having a technical issue. Try again later",
                [parsed_dict["from"][0]],
            )
    
    except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    
@app.post("/{organization}/message/add")
def add_message(message: Message, organization: str):
    try:
        # Retrieve phone numbers from the database
        numbers_data = db.get_phone_numbers()
        all_numbers = []

        # Flatten and clean the list of numbers
        for row in numbers_data:
            nums = row["numbers"].split(",")
            all_numbers.extend(nums)
        
        # Deduplicate and strip whitespace
        all_numbers = list(set(number.strip() for number in all_numbers))
        
        # Send the message via AfricasTalking
        AfricasTalking().send(message.shortcode, message.content, all_numbers)

        # Add the message to the database
        db.add_message(message.content, organization, message.shortcode, message.areas)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@app.get("/{organization}/messages/")
def get_messages(organization: str):
    if organization != "":
        results = db.get_messages(organization)
        return results
    else:
        return {"msg": "Organization not provided"}


@app.get("/areas")
def get_areas():
    areas = db.get_areas()
    return areas


@app.get("/numbers")
async def get_numbers():
    try:
        phone_numbers = db.get_phone_numbers()
        return {"numbers": phone_numbers}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/add_numbers_to_area")
async def add_numbers_to_area(area_and_numbers: AreaAndNumbers):
    if db.insert_new_number(area_and_numbers.area_name, area_and_numbers.numbers):
        return {"message": f"Numbers added to area '{area_and_numbers.area_name}' successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to add numbers to the database")
    
    
@app.post("/add_area")
async def add_area(area: Area):
    if db.add_area(area.name, area.numbers):
        return {"message": f"Area '{area.name}' added successfully with numbers: {area.numbers}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to add area to the database")


# @app.post("/test")
# async def receive_sms(file: UploadFile, organization: Annotated[str, Form()]):
#     return {"answer": file.filename, "orgn": organization}


# @app.get("/initdb")
# async def init_db(all: bool = False):
#     db.init_db()
#     db.insert_dummy_data()
#     if all:
#         wv_client.schema.delete_all()
#         print("Cleared Weaviate DB")
#     return {"msg": "DB Initialization successfull"}

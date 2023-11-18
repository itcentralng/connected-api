from fastapi import FastAPI
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
import os

load_dotenv()
app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:5173",
    "*",
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


@app.get("/")
def read_root():
    return {"app": "connected", "status": "ok"}


# ORGANIZATIONS
class AddOrganisation(BaseModel):
    email: str
    password: str


@app.post("/organization")
def register_org(organization: AddOrganisation):
    result = db.get_organization(organization.email)
    if result:
        if result["password"] == organization.password:
            return result
    else:
        return {"error": "Login unsuccessful"}


class Organization(BaseModel):
    name: str
    email: str
    password: str
    address: str
    description: str


@app.post("/register")
def register_org(organization: Organization):
    added_organization = db.add_organization(organization)
    return added_organization


@app.post("/organization/{organization}/uploadfile")
async def create_upload_file(
    file: UploadFile,
    organization: str,
    shortcode: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
):
    wv_class_name = f"{organization}_{file.filename.split('.')[0]}".replace(
        " ", ""
    ).replace("-", "")
    classes = [row["class"].upper() for row in wv_client.schema.get()["classes"]]
    print(classes)
    if wv_class_name.upper() not in classes:
        wv_create_class(wv_client, wv_class_name)
        try:
            with open(f"uploads/{file.filename}", "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            loader = PyPDFLoader(f"uploads/{file.filename}")
            doc = loader.load()
            wv_upload_doc(wv_client, doc, wv_class_name)

            # DB Operations
            added_file = db.add_file(
                {
                    "name": file.filename,
                    "organization": organization,
                    "weaviate_class": wv_class_name,
                    "description": description,
                }
            )
            added_shortcode = db.add_short_code(
                {
                    "shortcode": shortcode,
                    "organization_id": added_file["organization_id"],
                }
            )
            db.add_file_to_short_code(added_shortcode["id"], added_file["id"])
        except ValueError:
            return {"message": f"file: {file.filename} was not uploaded to server"}
        except AttributeError:
            return {"message": f"File: {file.filename} was not uploaded to weaviate"}
        finally:
            file.file.close()
    else:
        return {"msg": "File already exists"}
    return added_file


@app.post("organizations/{organization}/deletefile")
async def delete_files(organization: str, filename: str):
    wv_client.schema.delete_class()
    return {"message": f"{organization}_{filename.split('.')[0]}"}


# SHORT CODES
class ShortCode(BaseModel):
    short_code: int
    organization_id: int


@app.post("/{organization}/shortcode/add")
def register_short_code(short_code: ShortCode):
    added_short_code = db.add_short_code(short_code)
    return {"shortcode": added_short_code}


@app.get("/{organization}/shortcodes")
async def get_short_codes(organization: str):
    result = db.get_short_codes(organization)
    return {"short_codes": result}


@app.get("/{organization}/shortcode/{id}/delete")
def register_short_code(id):
    removed_short_code = db.delete_short_code(id)
    # ALSO REMOVE FILE
    return {"removed": removed_short_code}


class FileInfo(BaseModel):
    file_id: int


# SMS
@app.post("/sms")
async def receive_sms(request: Request):
    decoded_string = await request.body()
    parsed_dict = urllib.parse.parse_qs(decoded_string.decode("utf-8"))
    chat_history = []
    result = db.get_short_code(parsed_dict["to"][0])
    vectorstore = Weaviate(wv_client, result["weaviate_class"], "content")
    answer = ask_question(
        vectorstore,
        Cohere(temperature=0),
        parsed_dict["text"][0],
        chat_history,
    )
    print(parsed_dict["text"][0])
    print(answer)
    AfricasTalking().send(answer, [parsed_dict["from"][0]])
    return {"answer": answer}


class Message(BaseModel):
    content: str
    shortcode: str
    areas: list[str]


@app.post("/{organization}/message/add")
def add_message(message: Message, organization: str):
    added_message = db.add_message(
        message.content, organization, message.shortcode, message.areas
    )
    numbers = [row["numbers"].split(",") for row in added_message]
    AfricasTalking().send(message.content, numbers[0])
    return {"msg": "successfully sent messages"}


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


@app.post("/test")
async def receive_sms(file: UploadFile, organization: Annotated[str, Form()]):
    return {"answer": file.filename, "orgn": organization}


@app.get("/initdb")
async def init_db():
    db.init_db()
    db.insert_dummy_data()

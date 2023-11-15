from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from langchain.llms import OpenAI
from langchain.document_loaders import PyPDFLoader
from dotenv import load_dotenv
import shutil
import weaviate
from langchain.vectorstores import Weaviate
from utils.weaviate import upload_doc, create_class
from utils.weaviate import ask_question
from utils.db import (
    add_organization,
    add_short_code,
    delete_short_code,
    add_file,
    add_file_to_short_code,
    get_short_codes,
    get_organizations,
)

load_dotenv()
app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

wv_client = weaviate.Client(
    url="https://my-first-weaviate-cls-8ztyal2d.weaviate.network",
    auth_client_secret=weaviate.AuthApiKey(
        api_key="ZkGGaTH93uXiu3W1cc6vhq63ZNxSUE46S5pQ"
    ),
    additional_headers={
        "X-OpenAI-Api-Key": "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"
    },
)


@app.get("/")
def read_root():
    return {"app": "connected", "status": "ok"}


# ORGANIZATIONS
class Organization(BaseModel):
    name: str
    email: str
    password: str
    address: str
    description: str


@app.get("/organization")
def register_org():
    results = get_organizations()
    return {"organizations": results}


@app.post("/organization/add")
def register_org(organization: Organization):
    added_organization = add_organization(organization)
    return added_organization


@app.post("/organization/{orgn_id}/uploadfile")
async def create_upload_file(
    orgn_id: int, file: UploadFile, weaviate_class: str, description: str = ""
):
    file_name = file.filename.split("/")[1]
    loader = PyPDFLoader(f"data/{file_name}")
    doc = loader.load()
    try:
        with open(f"uploads/{file_name}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except:
        return {"message": f"file: {file_name} was not uploaded"}
    finally:
        file.file.close()

    schemas = [row["class"] for row in wv_client.schema.get()["classes"]]
    if weaviate_class not in schemas:
        create_class(wv_client, weaviate_class)

    try:
        upload_file = upload_doc(wv_client, doc, weaviate_class)
        print(upload_file)
    except:
        return {"message": f"Class: {weaviate_class} was not created"}

    try:
        added_file = add_file(
            {
                "name": file_name,
                "organization_id": orgn_id,
                "description": description,
                "weaviate_id": weaviate_class,
            }
        )
    except:
        return {"message": f"file: {file_name} was not added to DB"}

    return {"filename": added_file}


@app.post("organizations/{orgn_id}/uploadfiles")
async def create_upload_files(orgn_id: int, files: list[UploadFile]):
    return {"filenames": [file.filename for file in files]}


# SHORT CODES
class ShortCode(BaseModel):
    short_code: int
    organization_id: int


@app.post("/shortcode/add")
def register_short_code(short_code: ShortCode):
    added_short_code = add_short_code(short_code)
    return added_short_code


@app.get("/shortcode")
async def get_short_code():
    result = get_short_codes()
    return {"short_codes": result}


@app.get("/shortcode/{id}/delete")
def register_short_code(id):
    removed_short_code = delete_short_code(id)
    return removed_short_code


class FileInfo(BaseModel):
    file_id: int


@app.post("/shortcode/{short_code}/addfile")
async def create_upload_files(short_code: int, fileInfo: FileInfo):
    result = add_file_to_short_code(short_code, fileInfo.file_id)
    return {"file": result, "short_code": short_code}


# SMS
class SMS(BaseModel):
    id: str
    receiver: str
    sender: str
    type: str
    message: str
    message_id: str
    cost: str | None = None
    received_at: str
    status: str
    channel: str | None = None


@app.post("/sms")
async def receive_sms(sms: SMS):
    chat_history = []
    class_name = "Maternal_health"
    vectorstore = Weaviate(wv_client, class_name, "content")
    answer = ask_question(vectorstore, OpenAI, sms.message, chat_history)
    print(answer)
    return {"answer": answer}


class MyFile(BaseModel):
    file: dict


@app.post("/test")
async def receive_sms(file: UploadFile):
    return {"answer": file.filename}

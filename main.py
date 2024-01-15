from fastapi import FastAPI
from pydantic import BaseModel
from typing import Annotated
from fastapi import FastAPI, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain.llms.openai import OpenAI
from langchain.document_loaders import PyPDFLoader
from dotenv import load_dotenv
import shutil
import weaviate
from langchain.vectorstores import Weaviate
from utils import weaviate as wv
from utils import db
from utils.africastalking import AfricasTalking
import urllib.parse
import os

load_dotenv()
app = FastAPI()
origins = [
    os.environ.get("FRONTEND_URL"),
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
    additional_headers={"X-Openai-Api-Key": os.environ.get("OPENAI_API_KEY")},
)


# ORGANIZATION
class Organization(BaseModel):
    name: str
    email: str
    password: str
    address: str
    description: str


@app.post("/register")
def register_org(organization: Organization):
    added_organization = db.add_organization(organization)
    if "error" in added_organization:
        print(f"Error: {added_organization}")
    elif added_organization.data:
        print(f'Added Organization: {added_organization.data[0]["name"]}')

    return added_organization


class LoginCredential(BaseModel):
    email: str
    password: str


@app.post("/login")
def register_org(organization: LoginCredential):
    organization = db.get_organization(organization)
    if "error" in organization:
        print(f"Error: {organization}")
        return organization
    elif organization.data:
        return organization.data


# Format file name to be stored in weaviate
def format_file_name(organization, file):
    return f"{organization}_{file.filename.split('.')[0]}".replace(" ", "").replace(
        "-", ""
    )


# Get all classes (file names) currently in weaviate
def get_wv_classes():
    try:
        return [row["class"] for row in wv_client.schema.get()["classes"]]
    except Exception as error:
        print(error)
        return []


@app.post("/organization/{organization}/uploadfile")
async def create_upload_file(
    file: UploadFile,
    organization: str,
    shortcode: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
):
    found_shortcode = db.get_shortcode(shortcode)
    if "error" in found_shortcode:
        wv_class = format_file_name(organization, file).upper()
        wv_classes = get_wv_classes()
        print(wv_class)
        print(wv_classes)

        # Create weaviate class if it doesn't exist already
        if wv_class not in wv_classes:
            # create class
            wv.wv_create_class(wv_client, wv_class)
            # upload document to server (file system)
            wv.upload_doc(file)

            loader = PyPDFLoader(f"uploads/{file.filename}")
            doc = loader.load()
            # upload document to weaviate
            wv.wv_upload_doc(wv_client, doc, wv_class)

            # add file to database
            added_file = db.add_file(
                organization,
                {
                    "filename": file.filename,
                    "description": description,
                    "weaviate_class": wv_class,
                },
            )
            # add shortcode to database if there is no error adding file to database
            if "error" not in added_file:
                added_shortcode = db.add_shortcode(organization, shortcode)
                # add relationship between file and shortcode if no error adding shortcode to database
                if "error" not in added_shortcode:
                    response = db.add_file_to_shortcode(
                        added_shortcode.data[0]["id"], added_file.data[0]["id"]
                    )
                    return response
                else:
                    return {"error": added_shortcode["error"]}
            else:
                return {"error": added_file["error"]}
        else:
            print("File already exist in weaviate DB")
            return {"error": "File already exist in weaviate DB"}

    print("Error: shortcode already exists")
    return {"error": "shortcode already exists"}


class Message(BaseModel):
    content: str
    shortcode: str
    areas: list[str]


@app.post("/{organization}/message/")
def add_message(message: Message, organization: str):
    # get all numbers by selected areas
    numbers = [row["numbers"].split(",") for row in db.get_message_areas(message.areas)]
    all_numbers = []
    # merge all the numbers
    for nums in numbers:
        all_numbers = [*all_numbers, *nums]
    print(all_numbers)
    print(message.content)
    # send message to all numbers
    AfricasTalking().send(message.shortcode, message.content, all_numbers)

    # add message record to database
    added_message = db.add_message(
        message.content, organization, message.shortcode, message.areas
    )
    if "error" not in added_message:
        return {"msg": "successfully sent message"}
    return {"error": added_message["error"]}


@app.get("/{organization}/messages/")
def get_messages(organization: str):
    messages = db.get_messages(organization)
    if "error" not in messages:
        return messages.data
    return {"error": messages["error"]}


@app.get("/{organization}/files/")
def get_files(organization: str):
    files = db.get_files(organization)
    if "error" not in files:
        return files.data
    return {"error": files["error"]}


@app.get("/areas")
def get_areas():
    areas = db.get_areas()
    return areas.data


@app.get("/{organization}/shortcodes")
def get_shortcodes(organization: str):
    shortcodes = db.get_shortcodes(organization)
    print(shortcodes)
    if "error" not in shortcodes:
        return shortcodes.data
    else:
        return shortcodes


# SMS
@app.post("/sms")
async def receive_sms(request: Request):
    chat_history = []
    # parse received request body
    decoded_string = await request.body()
    parsed_dict = urllib.parse.parse_qs(decoded_string.decode("utf-8"))
    # get the specific shortcode the message was sent to
    result = db.get_shortcode_files(parsed_dict["to"][0].upper())

    # proceed if the shortcode exists and the message content is not empty
    if result.data and parsed_dict["text"][0]:
        print(f"Message received for -> {result.data['shortcodes']['shortcode']}")
        # initialize langchain weaviate client
        vectorstore = Weaviate(
            wv_client, result.data["files"]["weaviate_class"], "content"
        )
        # get the answer to the question
        answer = wv.ask_question(
            vectorstore,
            OpenAI(temperature=0),
            parsed_dict["text"][0],
            chat_history,
        )
        # print the list of weaviate classes for debugging purposes
        classes = get_wv_classes()
        print(classes)
        print(f'Message -> {parsed_dict["text"][0]}')
        print(f'Answering from -> {result.data["files"]["weaviate_class"]}')
        print(answer)
        AfricasTalking().send(parsed_dict["to"][0], answer, [parsed_dict["from"][0]])
    else:
        # give the user feedback
        AfricasTalking().send(
            parsed_dict["to"][0],
            "Sorry we are having a technical issue. Try again later",
            [parsed_dict["from"][0]],
        )
        print("Error: Short code does'nt exist")
    # pass


@app.get("/cleardb")
def clear_db():
    # clear weaviate database
    wv_client.schema.delete_all()
    print("Cleared weavite DB")
    # clear DB
    db.delete_all_organizations()
    print("Cleared supabase DB")

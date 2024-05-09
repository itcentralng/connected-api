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
    "https://connected-cohere-frontend.onrender.com",
    "https://connected-api-lja8.onrender.com",
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
def login_organization(organization: AddOrganisation):
    result = db.get_organization(organization.email)
    # print(result)
    try:
        if result:
            if result["password"] == organization.password:
                return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


# class uploadFile(BaseModel):
#     file: UploadFile = File(...)
#     organization: str
#     shortcode: str
#     organization_id:str
#     description: str
    


@app.post("/organization/{organization}/uploadfile")
async def create_upload_file(organization: str, file: UploadFile = Form(...), shortcode: str = Form(...), organization_id: str = Form(...)):
    
    wv_class_name = f"{organization}_{file.filename.split('.')[0]}".replace(
        " ", ""
    ).replace("-", "")
    classes = [row["class"].upper() for row in wv_client.schema.get()["classes"]]
    print(classes)
    print(file.filename)
    print(f"shortcode is: {shortcode}")
    # DB Operations
    added_file = db.add_file(
        {
            "name": file.filename,
            "organization": organization,
            "weaviate_class": wv_class_name,
        }
    )
    print('FILE ADDED: ', added_file)
    if added_file:
        added_shortcode = db.add_short_code(shortcode, organization_id)
        # print(added_file["weaviate_class"])
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
    print(organization_id)
    results = db.get_files(organization_id)
    print(results)
    return results


# SHORT CODES
class ShortCode(BaseModel):
    short_code: int
    organization_id: int


@app.post("/{organization}/shortcode/add")
def register_short_code(short_code: ShortCode, organization: str):
    added_short_code = db.add_short_code(short_code)
    print(f"Added {add_message} for {organization}")
    return {"shortcode": added_short_code}


@app.get("/{organization}/shortcodes")
async def get_short_codes(organization: str):
    results = db.get_short_codes(organization)
    print(f"shortcodes: {results}")
    return {"short_codes": results}


@app.get("/{organization}/shortcode/{id}/delete")
def register_short_code(id):
    removed_short_code = db.delete_short_code(id)
    # ALSO REMOVE FILE
    return {"removed": removed_short_code}


class FileInfo(BaseModel):
    file_id: int

class Sms(BaseModel):
    shortcode: str

# SMS
@app.post("/sms")
async def receive_sms(request: Request):
    decoded_string = await request.body()
    print(decoded_string)
    parsed_dict = urllib.parse.parse_qs(decoded_string.decode("utf-8"))
    print(parsed_dict)
    chat_history = []
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
        print(classes)
        print(parsed_dict)
        print(answer)
        AfricasTalking().send(parsed_dict["to"][0], answer, [parsed_dict["from"][0]])
        return {"answer": answer}
    else:
        AfricasTalking().send(
            parsed_dict["to"][0],
            "Sorry we are having a technical issue. Try again later",
            [parsed_dict["from"][0]],
        )
        print("Error: Short code does'nt exist")




class Message(BaseModel):
    content: str
    shortcode: str
    areas: list

        # Send message to all numbers in the specified areas using AfricasTalking

# @app.post("/{organization}/message/add")
# async def add_message(message: Message):
    
@app.post("/{organization}/message/add")
def add_message(message: Message, organization: str):
    # try:
    #     added_message = db.add_message(
    #     message.content, organization, message.shortcode, message.areas
    #     )
    #     print("Message areas: ", message.shortcode)
    #     numbers = [row["numbers"].split(",") for row in added_message]
    #     all_numbers = []
    #     for nums in numbers:
    #         all_numbers = [*all_numbers, *nums]
    #     print(all_numbers)
    #     print(message.content)
    #     AfricasTalking().send(message.shortcode, message.content, all_numbers)
    #     return {"msg": "successfully sent messages"}
    
    # except Exception as e:
    #     # Log or handle the exception as needed
    #     print("Error sending message:", e)
    #     raise HTTPException(status_code=500, detail="Failed to send message")
    # # get all numbers by selected areas
    numbers = [row["numbers"].split(",") for row in db.get_areas()]
    print("Numbers: ", numbers)
    all_numbers = []
    # merge all the numbers
    for nums in numbers:
        all_numbers = [*all_numbers, *nums]
    print(all_numbers)
    print(message.content)
    # send message to all numbers
    AfricasTalking().send(message.shortcode, message.content, all_numbers)
    print("success")

    # add message record to database
    added_message = db.add_message(
        message.content, organization, message.shortcode, message.areas
    )
    print("Added message: ", added_message)
    # if "error" not in added_message:
    #     return {"msg": "successfully sent message"}
    # return {"error": added_message["error"]}

    
    # # try:
    #     # Extract data from the message object
    #     content = message.content
    #     shortcode = message.shortcode
    #     areas = message.areas
    #     all_numbers = [number for area in areas for number in area.get("numbers").split(",")]
    #     # print(areas)
      
    #     # print(areas)
        
    #     print(all_numbers)
        
    #     # Split the numbers and iterate over each
    #     all_numbers = [number for numbers_str in areas for number in numbers_str.split(",")]
    #     print(all_numbers)        

    #     # Initialize AfricasTalking instance
    #     africas_talking = AfricasTalking()

    #     # Send message to each number
    #     for recipient in all_numbers:
    #         africas_talking.send(shortcode, content, [recipient])

    #     # Return success message
    #     return {"msg": "Successfully sent messages"}
    # except Exception as e:
    #     # Log or handle the exception as needed
    #     print("Error sending message:", e)
    #     raise HTTPException(status_code=500, detail="Failed to send message")


@app.get("/{organization}/messages/")
def get_messages(organization: str):
    if organization != "":
        results = db.get_messages(organization)
        print(results)
        return results
    else:
        print("Organization not provided")
        return {"msg": "Organization not provided"}


@app.get("/areas")
def get_areas():
    areas = db.get_areas()
    print(areas)
    return areas


class AreaAndNumbers(BaseModel):
    area_name: str
    numbers: str


@app.post("/add_numbers_to_area")
async def add_numbers_to_area(area_and_numbers: AreaAndNumbers):
    if db.insert_new_number(area_and_numbers.area_name, area_and_numbers.numbers):
        return {"message": f"Numbers added to area '{area_and_numbers.area_name}' successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to add numbers to the database")


@app.post("/test")
async def receive_sms(file: UploadFile, organization: Annotated[str, Form()]):
    return {"answer": file.filename, "orgn": organization}


@app.get("/initdb")
async def init_db(all: bool = False):
    db.init_db()
    db.insert_dummy_data()
    if all:
        wv_client.schema.delete_all()
        print("Cleared Weaviate DB")
    return {"msg": "DB Initialization successfull"}

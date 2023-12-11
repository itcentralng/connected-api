from langchain.chains import ConversationalRetrievalChain
import shutil
import os


# Upload file to server
def upload_doc(file):
    try:
        if not os.path.exists("uploads"):
            os.mkdir("uploads")

        with open(f"uploads/{file.filename}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"Uploaded file {file.filename} to server successfully")
    except Exception as error:
        print(f"File upload Error: {error}")


# Upload file to weaviate
def wv_upload_doc(wv_client, doc, class_name):
    try:
        wv_client.batch.configure(batch_size=300)
        with wv_client.batch as batch:
            for i, d in enumerate(doc):
                print(f"importing batch: {i+1}")
                properties = {"content": d.page_content}
                batch.add_data_object(data_object=properties, class_name=class_name)
        print(f"Uploaded file {class_name} to weaviate successfully")
    except Exception as error:
        print(f"Weaviate file upload Error: {error}")


# Create a class to store file in weaviate
def wv_create_class(wv_client, class_name):
    class_obj = {
        "class": class_name,
        "vectorizer": "text2vec-cohere",
        "moduleConfig": {
            "text2vec-cohere": {},
            "generative-cohere": {},
        },
    }

    wv_client.schema.create_class(class_obj)
    print(f"Schema {class_name} created successfully")


def ask_question(vectorstore, llm, question, chat_history):
    qa = ConversationalRetrievalChain.from_llm(
        llm,
        vectorstore.as_retriever(),
    )

    result = qa({"question": question, "chat_history": []})
    chat_history.append((question, result["answer"]))
    qa = None
    return result["answer"]

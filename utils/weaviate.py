import json
from langchain.chains import ConversationalRetrievalChain


def wv_upload_doc(wv_client, doc, class_name):
    wv_client.batch.configure(batch_size=300)
    with wv_client.batch as batch:
        for i, d in enumerate(doc):
            print(f"importing question: {i+1}")
            properties = {"content": d.page_content}
            batch.add_data_object(data_object=properties, class_name=class_name)
    print(f"File uploaded successfully")


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
    
    appended_question = f"DON'T ANSWER '{question}' IF IT'S NOT RELATED TO THE DOCUMENT and summarize my answer in a MAXIMUM of 130 characters ONLY. DO NOT SURPASS THE 130 CHARACTERS MARK. "

    result = qa({"question": appended_question, "chat_history": chat_history})
    chat_history.append((question, result["answer"]))
    qa = None
    return result["answer"]

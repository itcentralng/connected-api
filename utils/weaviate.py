import json
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate


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
    
        # Define your system instruction
    system_instruction = """
        Summarize your response in not more than 150 characters and DO NOT GO BEYOND YOUR PROVIDED DOCUMENT.
    """

    # Define your template with the system instruction
    template = (
        f"""
            {system_instruction}
            IGNORE QUESTION '{question}' IF IT'S NOT RELATED TO THE DOCUMENT PROVIDED 
            AND SUMMARISE EVERYTHING IN NOT MORE THAN 150 CHARACTERS
        """
    )
    
    # Create the prompt template
    CONDENSEprompt = PromptTemplate.from_template(template)

    
    qa = ConversationalRetrievalChain.from_llm(
        llm,
        vectorstore.as_retriever(),
        condense_question_prompt=CONDENSEprompt,
    )
    
    appended_question = f"SUMMARIZE YOUR ANSWER IN NOT MORE THAN 140 CHARACTERS AND REPLY QUESTION '{question}' WITH 'I CANNOT ANSWER THIS QUESTION AS IT IS NOT RELATED TO THE CONTEXT PROVIDED' IF IT'S NOT RELATED TO THE DOCUMENT."

    result = qa({"question": appended_question, "chat_history": chat_history})
    chat_history.append((question, result["answer"]))
    qa = None
    return result["answer"]

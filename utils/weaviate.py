import json
from fastapi import HTTPException
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate


def wv_upload_doc(wv_client, doc, class_name):
    try:
        wv_client.batch.configure(batch_size=300)
        with wv_client.batch as batch:
            for i, d in enumerate(doc):
                print(f"importing question: {i+1}")
                properties = {"content": d.page_content}
                batch.add_data_object(data_object=properties, class_name=class_name)
        print(f"File uploaded successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed add file")


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

def get_prompt(lang, question):
    
    prompts = {
        'eng':[
                   """
        Summarize your response in not more than 150 characters and DO NOT GO BEYOND YOUR PROVIDED DOCUMENT.
    """,
    
    f"""IF QUESTION '{question}' IS NOT IN ENGLISH TRANSLATE IT FIRST BEFORE PROCEEDING.
            
            IGNORE QUESTION '{question}' IF AND ONLY IF IT'S NOT RELATED TO THE DOCUMENT PROVIDED 
            AND SUMMARISE EVERYTHING IN NOT MORE THAN 150 CHARACTERS.
            
            RESPOND IN THE SAME LANGUAGE AS IN '{question}'
    """,
    f"SUMMARIZE YOUR ANSWER IN NOT MORE THAN 140 CHARACTERS AND REPLY QUESTION '{question}' WITH 'I CANNOT ANSWER THIS QUESTION AS IT IS NOT RELATED TO THE CONTEXT PROVIDED' ONLY AND ONLY IF IT'S NOT RELATED TO THE DOCUMENT."
    
        ],
        
    'hau':[
 """
    Taƙaita amsarku a cikin ba fiye da haruffa 150 ba kuma KAR KU WUCE WADANNAN TAKARDUN DA AKA BAYAR.
""",

f"""
    
    KA YI WATSAR DA TAMBAYA '{question}' IDAN KUMA IDAN TAMBAYAR BATA DA ALAKA DA TAKARDAR DA AKA BAYAR KUMA KA TAKAITA KOMAI A CIKIN BAI FIYE DA HARUFFA 150 BA.
    
    KA AMSA DA YAREN DA YAKE CIKIN TAMBAYA '{question}'""",
    
    """KA TAƘAITA AMSARKA A CIKIN BAI FIYE DA HARUFFA 140 BA KUMA KA AMSA DA 'BA ZAN IYA AMSA WANNAN TAMBAYA BA SABODA BATA DA ALAKA DA ABINDA AKA BAYAR' KAWAI IDAN BATA DA ALAKA DA TAKARDAR DA AKA BAYAR.
"""
        ]
    }
    
    
    
    return prompts[lang]


def ask_question(vectorstore, llm, question, chat_history, lang='hau'):
    
        # Define your system instruction
    system_instruction = get_prompt(lang, question)[0]

    # Define your template with the system instruction
    template = (
        f"""
            {system_instruction}
            
            {get_prompt(lang, question)[1]}
        """
    )
    
    # Create the prompt template
    CONDENSEprompt = PromptTemplate.from_template(template)

    
    qa = ConversationalRetrievalChain.from_llm(
        llm,
        vectorstore.as_retriever(),
        condense_question_prompt=CONDENSEprompt,
    )
    
    appended_question = get_prompt(lang, question)[2]

    result = qa({"question": appended_question, "chat_history": chat_history})
    chat_history.append((question, result["answer"]))
    qa = None
    return result["answer"]

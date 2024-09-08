from langchain.chat_models import ChatOpenAI
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor
from langchain.chains import LLMChain, ConversationalRetrievalChain
from langchain.utilities.serpapi import SerpAPIWrapper
from langchain.prompts import PromptTemplate
from fastapi import HTTPException
import weaviate

import os
import weaviate
from langchain.vectorstores import Weaviate
from langchain.embeddings.openai import OpenAIEmbeddings

# Weaviate client initialization
wv_client = weaviate.Client(
    url=os.environ.get("WEAVIATE_URL"),
    auth_client_secret=weaviate.AuthApiKey(api_key=os.environ.get("WEAVIATE_API_KEY")),
    additional_headers={
        "X-OpenAI-Api-Key": os.environ.get("OPENAI_API_KEY")
    }
)

def wv_create_class(wv_client, class_name):
    class_obj = {
        "class": class_name,
        "vectorizer": "text2vec-openai",
        "moduleConfig": {
            "text2vec-openai": {
                "model": "ada",
                "modelVersion": "002",
                "type": "text"
            },
            "generative-openai": {
                "model": "gpt-3.5-turbo"
            }
        },
    }
    wv_client.schema.create_class(class_obj)
    print(f"Schema {class_name} created successfully")


def wv_upload_doc(wv_client, doc, class_name):
    try:
        wv_client.batch.configure(batch_size=300)
        with wv_client.batch as batch:
            for i, d in enumerate(doc):
                print(f"importing document: {i+1}")
                properties = {"content": d.page_content}
                batch.add_data_object(data_object=properties, class_name=class_name)
        print(f"File uploaded successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add file: {str(e)}")

def get_prompt(lang, question):
    prompts = {
        'eng': [
            f"""IF QUESTION '{question}' IS NOT IN ENGLISH, TRANSLATE IT TO THAT LANGUAGE AND RESPOND. IGNORE QUESTION '{question}' 
            IF IT'S NOT RELATED TO THE DOCUMENT PROVIDED. RESPOND IN THE SAME LANGUAGE AS IN '{question}'""",
        ],
        'hau': [
            f"""KA YI WATSAR DA TAMBAYA '{question}' IDAN KUMA IDAN TAMBAYAR BATA DA ALAKA DA TAKARDAR DA AKA BAYAR. 
            KA AMSA DA YAREN DA YAKE CIKIN TAMBAYA '{question}'""",
        ]
    }
    print(prompts)
    return prompts[lang]

def do_search(input, language="hau"):
    model = 'gpt-3.5-turbo'
    # messages=[
    #     {"role": "system", "content": """You are a multilingual AI model named ConnectED which aims to bridge communication gaps by
    #      providing information that you have been trained with using the document uploaded by the organization. 
    #      You are to respond with an average of 140 text characters and MAXIMUM of 290 text characters only with what is provided to you 
    #      in the document/embeddings and do not go over what has not been taught to you.
    #      And always respond back in the language you were prompted with."""},
    #     {"role": "system", "content": """Always summarize responses within an average of 140 characters 
    #      and maximum of 290 characters in the same language you were prompted with."""}
    # ]
    # messages = [
    #     {"role": "system", "content": """You are a multilingual AI model named ConnectED, designed to provide accurate
    #      and concise responses within 290 characters based on the provided document. Always respond in the same language as the prompt.
    #      """}
    # ]
    messages = [
        {
            "role": "system", "content": """You are a multilingual AI model named ConnectED.
            Always identify yourself as ConnectED when asked. Provide accurate and 
            concise responses within 290 characters based on the provided document.
            Always respond in the same language as the prompt."""
        }
    ]



    search = SerpAPIWrapper()
    tools = [
        Tool(
            name="Search",
            func=search.run,
            description="useful for when you need to translate and answer questions that are not in {language}",
        )
    ]
    

    prefix = f"{messages[0]['content']} Answer the following questions as best you can. You have access to the following tools:"
    suffix = """When answering, you MUST speak in the following language: {language}.

    Question: {input}
    {agent_scratchpad}"""

    prompt = ZeroShotAgent.create_prompt(
        tools,
        prefix=prefix,
        suffix=suffix,
        input_variables=["input", "language", "agent_scratchpad"],
    )

    llm_chain = LLMChain(llm=ChatOpenAI(model=model, max_tokens=60, temperature=0.3), prompt=prompt)
    agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools)
    agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)

    return agent_executor.run(input=input, language=language)

def ask_question(vectorstore, llm, question, chat_history, lang='eng'):
    system_instruction = get_prompt(lang, question)[0]
    template = f"""
        {system_instruction}
        
        {get_prompt(lang, question)[0]}
    """
    condense_prompt = PromptTemplate.from_template(template)
    # print("Question: ",question)
    # print("Gotten Prompts: ", get_prompt(lang, question)[0])

    qa = ConversationalRetrievalChain.from_llm(
        llm,
        vectorstore.as_retriever(),
        condense_question_prompt=condense_prompt,
    )
    
    result = qa({"question": question, "chat_history": chat_history})
    chat_history.append((question, result["answer"]))
    return result["answer"]

# New helper function to create a Weaviate-based vectorstore for Langchain
# def create_weaviate_vectorstore(wv_client, class_name):
#     from langchain.vectorstores import Weaviate
#     return Weaviate(wv_client, class_name, "content")


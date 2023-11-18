# ConnectEd
## Tools used
**Cohere and Langchain:** Our large language model through Langchain to give personalized responses
**Weaviate:** Our vector store for embeddings generated through cohere's embedding model through Weaviate's text2vec-cohere plugin.
**FastAPI:** Our web framework for building APIs in python
**SQLite:** Our database for keeping organization information and other related data.
**ReactJS:** Our JavaScript frontend framework for the user dashboard.

## Datasets
1. 

## How to use Connected
1. Create an account on [AfricasTalking](https://account.africastalking.com/auth/register?next=%2Fapps%2Fsandbox).
2. Go to the simulator [click here](https://developers.africastalking.com/simulator).
3. Enter any number (can be any number its only active in the sandbox) and click connect.
4. Send a question to our service short codes (3525 for the WHO example).

## How to setup Connected locally on your computer
### The Backend
1. Create accounts in the following platforms: [Cohere](https://dashboard.cohere.com/welcome/login), [Weaviate](https://console.weaviate.cloud/), [AfricasTalking](https://account.africastalking.com/auth/register).
2. Clone the backend repo `git clone https://github.com/itcentralng/connected-cohere-hack.git`
3. Install the project dependencies `pip install -r requirements.txt`
4. Copy the contents of .env.example file into a new file .env (make sure you get your API keys from Cohere, Weaviate, AfricasTalking).
5. Create an empty db/ directory that will house the database
6. Run it `uvicorn main:app`
7. To initialize the database send an initial get request to `/initdb` end point.

***Note:*** AfricasTalking API key may take some time after creation before you can use it.

### The FrontEnd
1. Clone the frontend repo `git clone https://github.com/itcentralng/Connected-Frontend.git`
2. Install the project dependencies `npm install --legacy-peer-deps`
3. Run it `npm run dev`
4. Go to http://localhost:3000/

## To Dos
1. We will use an ORM instead of an SQLite client.
2. Do a lot of code refactoring.

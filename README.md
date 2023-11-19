# ConnectEd
## Tools used
**Cohere and Langchain:** Our large language model through Langchain to give personalized responses

**Weaviate:** Our vector store for embeddings generated through cohere's embedding model through Weaviate's text2vec-cohere plugin.

**FastAPI:** Our web framework for building APIs in python

**SQLite:** Our database for keeping organization information and other related data.

**ReactJS:** Our JavaScript frontend framework for the user dashboard.

## Datasets
1. The Pregnancy Book (St George’s University Hospitals NHS Foundation Trust) [download](https://www.stgeorges.nhs.uk/wp-content/uploads/2013/11/Pregnancy_Book_comp.pdf) | [source](https://www.stgeorges.nhs.uk/)

## How to use Connected
1. Create an account on [AfricasTalking](https://account.africastalking.com/auth/register?next=%2Fapps%2Fsandbox).
2. Go to the simulator [click here](https://developers.africastalking.com/simulator).
3. Enter any number (can be any number its only active in the sandbox) and click connect.
4. Send a question to our service short codes (3525 for the WHO example about pregnancy and baby care).

## How to setup Connected locally on your computer
### The Backend
1. Create accounts in the following platforms: [Cohere](https://dashboard.cohere.com/welcome/login), [Weaviate](https://console.weaviate.cloud/), [AfricasTalking](https://account.africastalking.com/auth/register), [Ngrok](https://ngrok.com/signup).
2. Clone the backend repo `git clone https://github.com/itcentralng/connected-cohere-hack.git`
3. Install the project dependencies `pip install -r requirements.txt`
4. Copy the contents of .env.example file into a new file .env (make sure you get your API keys from Cohere, Weaviate, AfricasTalking).
5. Follow the instruction on [Ngrok](https://ngrok.com/docs/getting-started/) to expose you local host (this is required to receive incoming SMS from AfricasTalking).
6. Enter your Ngrok address [here](https://account.africastalking.com/apps/sandbox/sms/inbox/callback) (make sure you add a `/sms` at the end of the address)
7. Create an empty db/ directory that will house the database
8. Run the project `uvicorn main:app`
9. To initialize the database send an initial get request to `[YOUR_API_URL]/initdb` end point (something like opening example.com/sms in your web browser).

***Note:*** AfricasTalking API key may take some time after creation before you can use it.

### The FrontEnd
1. Clone the frontend repo `git clone https://github.com/itcentralng/Connected-Frontend.git`
2. Install the project dependencies `npm install --legacy-peer-deps`
3. Create a `.env` file and add in your APIs (backend's) URL
4. Run it `npm run dev`
5. Go to http://localhost:3000/

***Note:*** To see the message sent from the frontend dashboard you need to use [AfricasTalking simulator](https://developers.africastalking.com/simulator) (Use one of the numbers from the `insert_dummy_data()` function, which can be found in the backend's `utils/db.py` file.

## To Dos
1. We will use an ORM instead of an SQLite client.
2. Do a lot of code refactoring.

# ConnectEd
ConnectEd is a platform that aims to address a significant knowledge gap by providing a centralized digital hub for various organizations to upload important updates and information. The platform would streamline the dissemination of crucial data to populations across wide geographic areas. 

The SMS functionality would ensure even those in remote, rural localities without consistent internet access could still receive and interact with timely advisories on topics such as agriculture, education, finance, and more. 

By partnering both information providers and citizens on one cohesive platform, ConnectED could virtually extend the reach of institutional messaging far beyond what traditional in-person community outreach allows.

***Note:*** We used render to host both our frontend and backend. Due to render's transient data policy for free accounts, our SQLite database is lost when our service runs down due to inactivity. For that reason our project is best run on a paid account or on localhost.
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
3. Create a virtual environment `python -m venv venv`
4. Activate the virtual environment. For Windows `./venv/Scripts/activate` and Linux/Mac/Git bash  `source venv/Scripts/activate`
5. Install the project dependencies `pip install -r requirements.txt`
6. Copy the contents of .env.example file into a new file .env (make sure you get your API keys from Cohere, Weaviate, AfricasTalking).
7. Get your Weaviate cluster URL and put it as your `WEAVIATE_URL` value in the .env file
8. Create an empty db/ directory that will house the database
9. Run the project `uvicorn main:app`
10. Follow the instruction on [Ngrok](https://ngrok.com/docs/getting-started/) to expose you local host (this is required to receive incoming SMS from AfricasTalking).
11. Enter your Ngrok address [here](https://account.africastalking.com/apps/sandbox/sms/inbox/callback) (make sure you add a `/sms` at the end of the address)

***Note:*** AfricasTalking API key may take some time after creation before you can use it.
***Note:*** To clear the database send a get request to `[YOUR_API_URL]/initdb` end point (something like opening `my_server_url.com/initdb` in your web browser or `my_server_url.com/initdb?all=True` to also clear the Weaviate DB).
***Note:*** OpenAI and Cohere have a rate limit on their free plan, so uploading a file will result in an error.

### The FrontEnd
1. Clone the frontend repo `git clone https://github.com/itcentralng/Connected-Frontend.git`
2. Install the project dependencies `npm install --legacy-peer-deps`
3. Copy the contents of .env.example file into a new file .env and add in your APIs (backend's) URL 
4. Run it `npm start`
5. Go to http://localhost:3000/

***Note:*** To see the message sent from the frontend dashboard you need to use [AfricasTalking simulator](https://developers.africastalking.com/simulator) (Use one of the numbers from the `insert_dummy_data()` function, which can be found in the backend's `utils/db.py` file.

## To Dos
1. We will use an ORM instead of an SQLite client.
2. Do a lot of code refactoring.

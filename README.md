# ConnectEd

ConnectEd is a platform that aims to address a significant knowledge gap by providing a centralized digital hub for various organizations to upload important updates and information. The platform would streamline the dissemination of crucial data to populations across wide geographic areas.

The SMS functionality would ensure even those in remote, rural localities without consistent internet access could still receive and interact with timely advisories on topics such as agriculture, education, finance, and more.

By partnering both information providers and citizens on one cohesive platform, ConnectED could virtually extend the reach of institutional messaging far beyond what traditional in-person community outreach allows.

## Tools used

**Cohere and Langchain:** Our large language model through Langchain to give personalized responses

**Weaviate:** Our vector store for embeddings generated through cohere's embedding model through Weaviate's text2vec-cohere plugin.

**FastAPI:** Our web framework for building APIs in python

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
4. Activate the virtual environment. For Windows `./venv/Scripts/activate` and Linux/Mac/Git bash `source venv/Scripts/activate`
5. Install the project dependencies `pip install -r requirements.txt`
6. Copy the contents of .env.example file into a new file .env (make sure you get your API keys from Cohere, Weaviate, AfricasTalking).
7. Get your Weaviate cluster URL and put it as your `WEAVIATE_URL` value in the .env file
8. Create an empty db/ directory that will house the database
9. Run the project `uvicorn main:app`
10. Follow the instruction on [Ngrok](https://ngrok.com/docs/getting-started/) to expose you local host (this is required to receive incoming SMS from AfricasTalking).
11. Enter your Ngrok address [here](https://account.africastalking.com/apps/sandbox/sms/inbox/callback) (make sure you add a `/sms` at the end of the address)

**_Note:_** AfricasTalking API key may take some time after creation before you can use it.
**_Note:_** OpenAI and Cohere have a rate limit on their free plan, so uploading a file will result in an error.

### The FrontEnd

1. Clone the frontend repo `git clone https://github.com/itcentralng/connected-frontend.git`
2. Install the project dependencies `npm install`
3. Copy the contents of .env.example file into a new file .env and add in your APIs (backend's) URL
4. Run it `npm start`
5. Open another terminal and run `npx convex dev`
6. Go to http://localhost:3000/

**_Note:_** To see the message sent from the frontend dashboard you need to use [AfricasTalking simulator](https://developers.africastalking.com/simulator) (Use one of the numbers from the `insert_dummy_data()` function, which can be found in the backend's `utils/db.py` file.)

**_Note:_** At the time of submission, the Africastalking API we are using is facing downtime and does not work due to the network outage caused by undersea cable.

import streamlit as st
import pandas as pd
from pymongo import MongoClient
from bson.codec_options import CodecOptions, DatetimeConversion
import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from pandasai import SmartDataframe
from streamlit_chat import message

# Load environment variables from .env file
load_dotenv()

# Function to chat with data
def chat_with_csv(df, query):
    groq_api_key = os.environ['GROQ_API_KEY']

    llm = ChatGroq(
        groq_api_key=groq_api_key, model_name="llama3-70b-8192",
        temperature=0.6
    )

    pandas_ai = SmartDataframe(df, config={"llm": llm})
    
    result = pandas_ai.chat(query)
    return result

# Set layout configuration for the Streamlit page
st.set_page_config(layout='centered')

# Set title for the Streamlit application
st.image("https://th.bing.com/th/id/R.82b66043d000db5fc7b5a6b7bb6c7573?rik=95SNyVMbLM55Hw&riu=http%3a%2f%2fyantra24x7.com%2fwp-content%2fuploads%2f2019%2f05%2flogo-yantra.png&ehk=FGxGnVixOaMHNP%2bM4OcL1M%2bFzZST%2bNnT1H9skt40Brc%3d&risl=&pid=ImgRaw&r=0", width=600)
#st.write("Welcome to our bot!")
st.markdown("<h6 style='text-align: left; '>Built by <a href='https://yantra24x7.com/'>YANTRA </a></h3>", unsafe_allow_html=True)

# Connect to MongoDB database
mongodb_url = os.environ['MONGODB_URL']
client = MongoClient(mongodb_url, datetime_conversion=DatetimeConversion.DATETIME_AUTO)

# Fetch all database names
database_names = client.list_database_names()

# Sidebar for Database and Collection selection
with st.sidebar:
    selected_db = st.selectbox("Select a database", database_names)

    # Fetch collections from the selected database
    if selected_db:
        collection_names = client[selected_db].list_collection_names()
        selected_collection = st.selectbox("Select a collection", collection_names)

# Function to fetch data from a collection
def fetch_data(db_name, collection_name):
    db = client[db_name]
    collection = db.get_collection(collection_name, codec_options=CodecOptions(tz_aware=True, datetime_conversion=DatetimeConversion.DATETIME_AUTO))
    cursor = collection.find()
    data = []
    for document in cursor:
        document['_id'] = str(document['_id'])  # Convert ObjectId to string
        data.append(document)
    return pd.DataFrame(data)

# Fetch data from the selected collection
if selected_db and selected_collection:
    df = fetch_data(selected_db, selected_collection)

    if not df.empty:
        st.subheader("Preview of the Data")
        st.dataframe(df.head(5))

    # Initialize chat history in session state
    if 'history' not in st.session_state:
        st.session_state['history'] = []

    if 'generated' not in st.session_state:
        st.session_state['generated'] = ["Hello! Ask me anything about the data in the selected collection 🤗"]

    if 'past' not in st.session_state:
        st.session_state['past'] = ["Hey! 👋"]

    # Container for the chat history
    response_container = st.container()
    # User's text input
    user_input = st.chat_input("Send a message", key='input')

    # Process user input and generate response
    if user_input:
        st.session_state['past'].append(user_input)
        output = chat_with_csv(df, user_input)

        if isinstance(output, pd.DataFrame):
            st.session_state['generated'].append(output)
        else:
            st.session_state['generated'].append(output)

    # Display chat history
    if st.session_state['generated']:
        with response_container:
            for i in range(len(st.session_state['generated'])):
                message(st.session_state["past"][i], is_user=True, key=str(i) + '_user', avatar_style="no-avatar")
                if isinstance(st.session_state["generated"][i], pd.DataFrame):
                    st.dataframe(st.session_state["generated"][i])
                elif os.path.exists(st.session_state["generated"][i]):
                    st.image(st.session_state["generated"][i])
                else:
                    message(st.session_state["generated"][i], key=str(i),avatar_style="no-avatar", logo='https://is4-ssl.mzstatic.com/image/thumb/Purple113/v4/cb/49/00/cb4900e0-e38b-474c-dd29-f770b307a7f7/source/512x512bb.jpg')

# Close MongoDB client
client.close()

import os
import sqlite3
import streamlit as st

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def get_sql_query_from_text(text):
    # Initialize the ChatGroq model
    groq_system_prompt = ChatPromptTemplate.from_template("""t
        You are a SQL query generator. You will be given a natural language text and you need to generate a SQL query based on that text.
        Example -How many entries are there in the table?:
            SQL Command will be SELECT COUNT(*) FROM table_name;
        also the sql code should be in the form of a string and should not contain any extra spaces or new lines and
        should not have ''' in beginning and end. Convert the following text into a SQL query: {user_query}.
        No preamble, no explanation, just the valid SQL query.
      """)

    # Generate SQL query from the input text
    model="llama3-8b-8192"
    llm = ChatGroq(
         groq_api_key = st.secrets["GROQ_API_KEY"],
         model_name=model,
    )
    chain = groq_system_prompt | llm | StrOutputParser()
    sql_query = chain.invoke({"user_query": text})

    return sql_query


def create_db_from_sql_file(sql_file):
    try:
        # Read SQL script
        sql_script = sql_file.read().decode("utf-8")

        # Create temporary SQLite DB
        temp_db_path = tempfile.NamedTemporaryFile(delete=False, suffix=".db").name
        with sqlite3.connect(temp_db_path) as conn:
            conn.executescript(sql_script)
        return temp_db_path, None
    except Exception as e:
        return None, f"Error while processing SQL file: {e}"

def save_uploaded_db_file(uploaded_file):
    try:
        temp_db_path = tempfile.NamedTemporaryFile(delete=False, suffix=".db").name
        with open(temp_db_path, "wb") as f:
            f.write(uploaded_file.read())
        return temp_db_path, None
    except Exception as e:
        return None, f"Error while saving DB file: {e}"

def run_query_on_db(db_path, sql_query):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(sql_query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return columns, rows
    except Exception as e:
        return None, f"SQL Error: {e}"
    
def main():
    st.set_page_config(page_title="Text-to-SQL (DB Only)", layout="wide")
    st.title("📂 SQLite Text-to-SQL App")
    st.markdown("Upload a `.db` file (SQLite) and ask questions about your data using plain English.")

    uploaded_file = st.file_uploader("Upload your SQLite `.db` file", type=["db", "sql"])
    user_input = st.text_area("Ask a question:", height=80)

    if st.button("Submit") and uploaded_file and user_input:
        # Determine file type and process accordingly
        if uploaded_file.name.endswith(".db"):
            db_path, error = save_uploaded_db_file(uploaded_file)
        elif uploaded_file.name.endswith(".sql"):
            db_path, error = create_db_from_sql_file(uploaded_file)
        else:
            error = "Unsupported file type."

        if error:
            st.error(error)
            return

        sql_query = get_sql_query_from_text(user_input)
        st.code(sql_query, language="sql")

        # Execute query
        columns, result = run_query_on_db(db_path, sql_query)

        if isinstance(result, str):  # error message
            st.error(result)
        elif result:
            import pandas as pd
            df = pd.DataFrame(result, columns=columns)
            st.dataframe(df)
        else:
            st.info("No data returned.")

if __name__ == "__main__":
    main()

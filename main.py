import os
import sqlite3
import streamlit as st
import pandas as pd
import tempfile
from dotenv import load_dotenv, find_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

groq_api_key = st.secrets["GROQ_API_KEY"]

def get_sql_query_from_text(user_query, schema):
    prompt = ChatPromptTemplate.from_template("""
You are a SQL query generator. You're an expert Analyst proficient in querying Database, finding insights and solving problems related to Database.
You task is to query the data and sql based on provided schema, files and user query mention in the promt{user_query}.

schema of the database:
{schema}

Given the above schema, generate a valid SQL query for this prompt of user from the provided db and sql file based on this schema:


SQL Command (no preamble, no explanation, just one-line valid SQL query string without quotes):
""")

    llm = ChatGroq(groq_api_key=groq_api_key, model_name="llama3-8b-8192")
    chain = prompt | llm | StrOutputParser()
    sql_query = chain.invoke({"user_query": user_query, "schema": schema})
    return sql_query

def extract_db_schema(db_path):
    schema = ""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            for table in tables:
                schema += f"Table: {table}\n"
                cursor.execute(f"PRAGMA table_info({table});")
                columns = cursor.fetchall()
                for col in columns:
                    schema += f"  {col[1]} ({col[2]})\n"
            return schema
    except Exception as e:
        return f"Error extracting schema: {e}"

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
    st.set_page_config(page_title="Text-to-SQL", layout="wide")
    st.title("📂 SQLite Text-to-SQL App")
    st.markdown("Upload a `.sql` file (SQLite) and ask questions about your data using plain English.")

    uploaded_file = st.file_uploader("Upload your SQLite `.sql` file", type=["sql", "db"])
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
        
        schema = extract_db_schema(db_path)
        st.expander("🔍 View Extracted Schema").write(schema)

        sql_query = get_sql_query_from_text(user_input, schema)
        
        # Execute query
        columns, result = run_query_on_db(db_path, sql_query)

        if isinstance(result, str):  # error message
            st.error(result)
        elif result:

            df = pd.DataFrame(result, columns=columns)
            st.dataframe(df)
        else:
            st.info("No data returned.")

if __name__ == "__main__":
    main()

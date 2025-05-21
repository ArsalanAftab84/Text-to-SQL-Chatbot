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
        Example 1-How many entries are there in the table?:
            SQL Command will be SELECT COUNT(*) FROM student;
        Example 2-How many students are there in the course of Data Sciences?:
             SQL Command will be SELECT COUNT(*) FROM student WHERE course = 'Data Sciences';
        also the sql code should be in the form of a string and should not contain any extra spaces or new lines and
        should not have ''' in beginning and end. Convert the following text into a SQL query: {user_query}.
        No preamble, no explanation, just the valid SQL query.
      """)

    # Generate SQL query from the input text
    model="llama3-8b-8192"
    llm = ChatGroq(
         groq_api_key=os.environ.get("GROQ_API_KEY"),
         model_name=model,
    )
    chain = groq_system_prompt | llm | StrOutputParser()
    sql_query = chain.invoke({"user_query": text})

    return sql_query


def get_data_from_database(sql_query):
    database="student.db"
    with sqlite3.connect(database) as conn:
        return conn.execute(sql_query).fetchall()
    

def main():
    st.set_page_config(page_title="Text-to-SQL Application", page_icon=":guardsman:", layout="wide")
    print("Welcome to the Text-to-SQL Application!")
    st.title("Text-to-SQL Application")

    user_input = st.text_area("Enter your SQL query here:", height=80)
    submit=st.button("Submit")
    if submit:
        sql_query = get_sql_query_from_text(user_input)
        st.write(f"Generated SQL query: {sql_query}")
        retrieve_data = get_data_from_database(sql_query)
        st.header("Retrieved Data:")
        for row in retrieve_data:
            st.header(row)

if __name__ == "__main__":
    main()
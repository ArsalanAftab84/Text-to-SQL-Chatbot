import sqlite3

connection= sqlite3.connect('student.db')


# Create a cursor object using the connection
cursor = connection.cursor()

# Create a table
create_table_query='''
CREATE TABLE IF NOT EXISTS student (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(25),
    course VARCHAR(25),
    section VARCHAR(25),
    marks INTEGER
);
'''
cursor.execute(create_table_query)


# Insert data into the table

insert_data_query='''
INSERT INTO student (name, course, section, marks)
VALUES (?, ?, ?, ?)
'''
data = [
    ('Student1', 'Data Science', 'A', 85),
    ('Student2', 'Data Science', 'B', 90),
    ('Student3', 'Data Science', 'A', 95),
    ('Student4', 'Devops', 'C', 80),
    ('Student5', 'Devops', 'B', 75),
]

cursor.executemany(insert_data_query, data)
connection.commit()

# Fetch data from the table
fetch_data_query='''
SELECT * FROM STUDENT
'''
dt = cursor.execute(fetch_data_query)

for row in dt:
    print(row)

if connection:
    connection.close()
    print("Connection closed")
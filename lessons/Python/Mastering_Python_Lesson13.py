#!/usr/bin/env python
# coding: utf-8

# In[1]:


"""
Python mastery: connecting your code to databases.
Welcome to Lesson 13: Working with Databases (SQLite and MySQL).
This is where Python moves from analyzing data → to storing, retrieving, and managing it persistently — just like in your Django and health data projects.

Learning Goals
By the end of this lesson, you’ll be able to:
Understand how databases store structured data
Create and use a database in SQLite (built-in)
Connect to MySQL using Python
Execute CRUD operations (Create, Read, Update, Delete)
Integrate databases with pandas for analysis

What Is a Database?
A database is an organized collection of data that allows:
Efficient storage and retrieval
Consistent structure using tables
Access via SQL (Structured Query Language)
Think of a table as a spreadsheet:

+----+---------+-----+-----------+
| id | name    | age | heart_rate|
+----+---------+-----+-----------+
| 1  | Alice   | 52  | 78        |
| 2  | Bob     | 47  | 88        |
+----+---------+-----+-----------+
SQLite — Your First Python Database
SQLite comes built into Python. No setup needed.
It stores data in a single .db file.
Example: Create and Use an SQLite Database
"""

import sqlite3

# Connect (creates a new DB if not exists)
conn = sqlite3.connect("heart_data.db")
cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    heart_rate INTEGER
)
""")

# Insert data
cursor.execute("INSERT INTO patients (name, age, heart_rate) VALUES (?, ?, ?)", 
               ("Alice", 52, 78))
cursor.execute("INSERT INTO patients (name, age, heart_rate) VALUES (?, ?, ?)", 
               ("Bob", 47, 88))

conn.commit()   # save changes


# In[2]:


# Read data

cursor.execute("SELECT * FROM patients")
rows = cursor.fetchall()

for row in rows:
    print(row)


# In[3]:


# Update and delete

cursor.execute("UPDATE patients SET heart_rate = 82 WHERE name = 'Bob'")
cursor.execute("DELETE FROM patients WHERE name = 'Alice'")
conn.commit()


# In[4]:


# Close connection

conn.close()


# In[5]:


# Using pandas with SQLite
# You can read SQL tables straight into pandas!

import pandas as pd
import sqlite3

conn = sqlite3.connect("heart_data.db")

df = pd.read_sql_query("SELECT * FROM patients", conn)
print(df)

conn.close()


# In[6]:


# Error handling with databases

try:
    conn = sqlite3.connect("heart_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients")
except sqlite3.Error as e:
    print("Database error:", e)
finally:
    conn.close()


# In[7]:


# Real-world Use Case - Health Tracker

import sqlite3
import pandas as pd

# Connect
conn = sqlite3.connect("health_tracker.db")
cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS daily_log (
    date TEXT,
    steps INTEGER,
    sleep_hours REAL,
    heart_rate INTEGER
)
""")

# Insert records
data = [
    ("2025-10-21", 8500, 7.0, 78),
    ("2025-10-22", 9100, 6.5, 82),
    ("2025-10-23", 10400, 7.8, 76)
]
cursor.executemany("INSERT INTO daily_log VALUES (?, ?, ?, ?)", data)
conn.commit()

# Load into pandas
df = pd.read_sql_query("SELECT * FROM daily_log", conn)
print(df)

conn.close()


# In[8]:


# Querying with pandas
# You can now perform analysis directly:

print("Average heart rate:", df["heart_rate"].mean())
print("Average steps:", df["steps"].mean())


# In[9]:


# Or visualize it

import matplotlib.pyplot as plt

plt.plot(df["date"], df["steps"], label="Steps", marker="o")
plt.plot(df["date"], df["heart_rate"], label="Heart Rate", marker="s")
plt.legend()
plt.title("Health Tracker Data from SQLite")
plt.show()

"""
| Task                  | Tool                         | Example                                          |
| --------------------- | ---------------------------- | ------------------------------------------------ |
| Connect to database   | `sqlite3.connect()`          | `conn = sqlite3.connect("my.db")`                |
| Run SQL query         | `cursor.execute()`           | `SELECT * FROM patients`                         |
| Fetch data            | `cursor.fetchall()`          | iterate over rows                                |
| Integrate with pandas | `pd.read_sql_query()`        | `pd.read_sql_query("SELECT * FROM table", conn)` |
| Use MySQL             | `mysql.connector`            | connect with host/user/password                  |
| CRUD                  | Create, Read, Update, Delete | SQL statements                                   |

"""


# In[ ]:





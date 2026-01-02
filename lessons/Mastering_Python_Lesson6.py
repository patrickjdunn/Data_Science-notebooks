#!/usr/bin/env python
# coding: utf-8

# In[1]:


"""
you’re making real progress now 

Welcome to Lesson 6: Working with Files — one of the most practical Python skills you’ll ever learn.

Almost every real-world Python program needs to read, write, and process data from files — like text files, CSV spreadsheets, or JSON data.

Learning Goals

By the end of this lesson, you’ll be able to:
Open and read text files safely
Write and append to files
Work with CSV data using csv and pandas
Handle JSON files for structured data

Reading and Writing Text Files

Let’s start with plain text (.txt) files — the simplest file type.

Writing a File
"""

# Open a file in write mode
file = open("notes.txt", "w")

file.write("This is my first line.\n")
file.write("Python makes file handling easy!\n")

file.close()

# This creates a file called notes.txt in your working directory.


# In[2]:


# Reading a File

file = open("notes.txt", "r")

content = file.read()
print(content)

file.close()


# In[3]:


"""
Using the with Statement (Best Practice)

Python’s recommended way — it automatically closes the file:
"""

with open("notes.txt", "r") as file:
    for line in file:
        print(line.strip())

# strip() removes extra newline characters at the end.


# In[4]:


# Appending to an Existing File

with open("notes.txt", "a") as file:
    file.write("Adding one more line!\n")

"""
| Mode  | Meaning                            |
| ----- | ---------------------------------- |
| `'r'` | Read (error if file doesn’t exist) |
| `'w'` | Write (overwrites file)            |
| `'a'` | Append (adds to end)               |

"""


# In[5]:


"""
Working with CSV Files

CSV = Comma-Separated Values — the most common format for spreadsheets.

Writing a CSV File
"""

import csv

with open("patients.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Name", "Age", "HeartRate"])
    writer.writerow(["Alice", 52, 72])
    writer.writerow(["Bob", 47, 88])


# In[6]:


# Reading a CSV File

import csv

with open("patients.csv", "r") as file:
    reader = csv.reader(file)
    for row in reader:
        print(row)


# In[7]:


# CSV as Dictionary (better readability)

import csv

with open("patients.csv", "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        print(f"{row['Name']} has a heart rate of {row['HeartRate']} bpm.")


# In[ ]:


# Add section on pandas


# In[9]:


"""
Working with JSON Files

JSON = JavaScript Object Notation, used for structured data (like APIs).

Writing JSON
"""

import json

patient = {
    "name": "Charlie",
    "age": 63,
    "heart_rate": 82,
    "medications": ["Lisinopril", "Metformin"]
}

with open("patient.json", "w") as file:
    json.dump(patient, file, indent=4)


# In[10]:


# Reading JSON

import json

with open("patient.json", "r") as file:
    data = json.load(file)

print(data)
print(data["medications"])


# In[11]:


"""
File Handling Errors

Always anticipate problems — missing files, permissions, etc.
"""

try:
    with open("missing.txt", "r") as file:
        content = file.read()
except FileNotFoundError:
    print("File not found. Please check the filename.")


# In[12]:


# Mini Project: Health Log

import csv

# Step 1: Write data
with open("daily_health.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Date", "Steps", "SleepHours"])
    writer.writerow(["2025-10-25", 9200, 7.5])
    writer.writerow(["2025-10-24", 7500, 6.8])

# Step 2: Read data
with open("daily_health.csv", "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        print(f"On {row['Date']}, you walked {row['Steps']} steps and slept {row['SleepHours']} hours.")


# In[ ]:


"""
| File Type | Library           | Typical Use                 |
| --------- | ----------------- | --------------------------- |
| `.txt`    | built-in `open()` | Notes, logs                 |
| `.csv`    | `csv`, `pandas`   | Tables, spreadsheets        |
| `.json`   | `json`            | API data, structured config |

"""


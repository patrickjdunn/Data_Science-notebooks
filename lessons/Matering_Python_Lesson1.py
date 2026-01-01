#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
The Plan to Master Python
Phase 1: Core Foundations

You’ll learn how Python thinks:
Variables and data types
Strings, lists, tuples, sets, and dictionaries
Control flow: if/else, loops, and functions
Input/output and basic error handling
Goal: Be able to write small, useful scripts that process data and make decisions.
    
"""


# In[1]:


# Copy this code and paste it in your IDE  
# my_first_script.py

# This is a comment. Python ignores lines that start with #
# Let's print something to the screen

print("Hello, world! Welcome to Python mastery.")

"""
Python interpreted it line by line (not compiled, like C++ or Java).
It executed the print() function — which sent text to the console.

"""


# In[2]:


# Try it yourself. Type this code.

name = "Alex"
print("Hi", name)


# In[3]:


# Now type this. This tells you name is a string type — text data stored in memory.

type(name)


# In[4]:


# Now type this, using f-strings, one of Python’s most powerful formatting tools.

first_name = "Alex"
age = 35
city = "Dallas"

print(f"My name is {first_name}, I’m {age} years old, and I live in {city}.")


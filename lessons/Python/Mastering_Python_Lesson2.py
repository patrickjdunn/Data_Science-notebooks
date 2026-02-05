#!/usr/bin/env python
# coding: utf-8

# In[12]:


"""
Lesson 2: Variables and Data Types
Learning Goals
By the end of this lesson, you’ll be able to:
Create and name variables correctly.
Understand Python’s core data types.
Perform operations with numbers and strings.
Convert between types safely.

"""


# In[1]:


"""
What is a Variable?

A variable is like a labeled box in memory that stores a value.
"""

age = 35
name = "Alex"
height = 1.75


# In[ ]:


"""
Think of this as:
age → box labeled “age” contains the number 35
name → contains the string "Alex"
height → contains the floating-point number 1.75

Variable Naming Rules

Allowed:

Letters, numbers, underscores (_)

Must start with a letter or underscore

Not allowed:

Starting with a number (1name = "Alex")

Using spaces or special symbols (my name = "Alex")

"""


# In[2]:


# Examples of good names:

first_name = "Alex"
age_in_years = 35
total_score = 99.5


# In[ ]:


"""
| Type    | Example           | Description     |
| ------- | ----------------- | --------------- |
| `int`   | `42`              | Whole numbers   |
| `float` | `3.14`            | Decimal numbers |
| `str`   | `"Hello"`         | Text data       |
| `bool`  | `True` or `False` | Logical values  |

"""


# In[4]:


# You can check any variable’s type with:

type(name)


# In[5]:


x = 42
print(type(x))  # <class 'int'>


# In[6]:


"""
Working with Numbers

Python can do math easily:
"""

a = 10
b = 3

print(a + b)  # addition
print(a - b)  # subtraction
print(a * b)  # multiplication
print(a / b)  # division (always float)
print(a // b) # integer division
print(a % b)  # remainder
print(a ** b) # exponentiation


# In[14]:


"""
Working with Strings

Strings are text inside quotes ' ' or " ".
"""

greeting = "Hello"
name = "Alex"

message = greeting + " " + name
print(message)  # Hello Alex


# In[8]:


# You can also use f-strings for cleaner formatting:

print(f"{greeting}, {name}! How are you?")


# In[9]:


# String Operations

word = "Python"
print(word.upper())     # PYTHON
print(word.lower())     # python
print(word.startswith("Py"))  # True
print(len(word))        # 6


# In[10]:


"""
Type Conversion (Casting)

Python allows converting between compatible types.
"""

x = "10"
y = int(x)     # convert string to integer
z = float(y)   # convert integer to float
print(z)       # 10.0


# In[11]:


# User information
name = "Taylor"
age = 29
height = 1.75

# Calculate age next year
next_year_age = age + 1

# Output message
print(f"{name} is {age} years old and will be {next_year_age} next year.")
print(f"{name} is {height} meters tall.")


# In[ ]:


"""
| Concept           | Example                     |
| ----------------- | --------------------------- |
| Create a variable | `x = 5`                     |
| Check type        | `type(x)`                   |
| Basic math        | `+ - * / // % **`           |
| String formatting | `f"Hello {name}"`           |
| Convert types     | `int()`, `float()`, `str()` |

"""


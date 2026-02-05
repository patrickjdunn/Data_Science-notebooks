#!/usr/bin/env python
# coding: utf-8

# In[1]:


"""
Welcome to Lesson 8: Modules and Packages — how Python organizes and reuses code efficiently.

This lesson will teach you how to go from single-file scripts to real software projects like your Django app.

Learning Goals

By the end of this lesson, you’ll be able to:
Understand what modules and packages are
Import and use modules (built-in and custom)
Create your own modules and packages
Understand __init__.py and relative imports
Use the Python Standard Library effectively

What is a Module?

A module is simply a .py file that contains Python code — functions, classes, or variables — that you can import and reuse.

Example:
Let’s say you have a file called math_utils.py:
"""

# math_utils.py
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

# You can use this in another file


# In[ ]:


# main.py
import math_utils

result = math_utils.add(10, 5)
print(result)


# In[3]:


"""
Different Ways to Import
Import entire module
"""

import math
print(math.sqrt(16))


# In[4]:


# Import specific function

from math import sqrt
print(sqrt(25))


# In[5]:


# Rename a module (alias)

import math as m
print(m.pi)


# In[6]:


# Import multiple items

from math import sin, cos, tan


# In[7]:


# Import all (not recommended)

from math import *


# In[ ]:


"""
| Module     | Purpose                  | Example                 |
| ---------- | ------------------------ | ----------------------- |
| `math`     | Math functions/constants | `math.sqrt(9)`          |
| `random`   | Random numbers           | `random.randint(1, 10)` |
| `datetime` | Dates and times          | `datetime.date.today()` |
| `os`       | File system              | `os.listdir()`          |
| `sys`      | System info              | `sys.version`           |
| `json`     | JSON handling            | `json.dump()`           |
| `csv`      | CSV handling             | `csv.reader()`          |

"""


# In[8]:


import random

number = random.randint(1, 100)
print(f"Your random number is {number}")


# In[9]:


"""
Creating and Using Your Own Modules

Let’s do a quick example.

Step 1 — Create a file called heart_utils.py
"""

# heart_utils.py
def bpm_category(bpm):
    if bpm < 100:
        return "Normal"
    else:
        return "Tachycardia"


# In[ ]:


# Create another file called main.py

import heart_utils

print(heart_utils.bpm_category(85))
print(heart_utils.bpm_category(110))


# In[ ]:


"""
What is a Package?

A package is a collection of modules organized in folders.
Every package contains a special file called __init__.py.

Example structure:

health/
    __init__.py
    heart.py
    bp.py

"""


# In[10]:


# heart.py

def bpm_status(bpm):
    return "Normal" if bpm < 100 else "High"


# In[11]:


# bp.py

def bp_status(sys, dia):
    if sys < 120 and dia < 80:
        return "Normal"
    else:
        return "Elevated"


# In[ ]:


# main.py

from health import heart, bp

print(heart.bpm_status(95))
print(bp.bp_status(135, 85))

# Folders + __init__.py = Python package.


# In[ ]:


"""
The __init__.py File

The presence of __init__.py tells Python “this directory is a package.”

It can be empty, or it can initialize imports:
"""
# health/__init__.py
from .heart import bpm_status
from .bp import bp_status


# In[ ]:


# Then you can import directly:

from health import bpm_status, bp_status


# In[12]:


"""
The Python Path

Python needs to know where to find your modules.
It looks in:

The current working directory

Installed site packages

Paths in sys.path

You can check it with:
"""

import sys
print(sys.path)


# In[ ]:


"""
| Concept     | Description               | Example                 |
| ----------- | ------------------------- | ----------------------- |
| **Module**  | A single `.py` file       | `import math_utils`     |
| **Package** | Folder with `__init__.py` | `from health import bp` |
| **Import**  | Bring code into a script  | `import mymodule`       |
| **Alias**   | Rename module             | `import math as m`      |

"""


#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
Python Collections
Learning Goals

By the end of this lesson, you’ll know how to:
Create and manipulate lists, tuples, sets, and dictionaries
Access, modify, and loop through their elements
Know when to use each type

"""


# In[1]:


# Lists — Ordered and Changeable

# Lists are ordered, mutable (changeable), and allow duplicates. There are identified by using [brackets]

fruits = ["apple", "banana", "cherry"]
print(fruits)


# In[2]:


# Access items

print(fruits[0])    # apple (first item)
print(fruits[-1])   # cherry (last item)


# In[3]:


# Modify items

fruits[1] = "blueberry"
print(fruits)  # ['apple', 'blueberry', 'cherry']


# In[4]:


# Add or remove

fruits.append("mango")       # add at end
fruits.insert(1, "pear")     # insert at index 1
fruits.remove("apple")       # remove by value
print(fruits)


# In[5]:


# Loop through

for fruit in fruits:
    print(fruit)


# In[6]:


# Useful functions

numbers = [10, 20, 30, 40]
print(len(numbers))      # number of items
print(sum(numbers))      # total
print(max(numbers))      # largest
print(min(numbers))      # smallest


# In[7]:


"""
Tuples - Ordered and unchangeable
Tuples are like lists, but immutable (cannot be changed after creation). They are identified by using (parentheses)

Use tuples for fixed data (like coordinates, RGB colors, etc.).
"""

coordinates = (10.5, 20.7)
print(coordinates[0])  # 10.5


# In[ ]:





# In[8]:


"""
Sets — Unordered and Unique

Sets are unordered, unindexed, and only contain unique items. They are identified by using {curly braces}
"""

colors = {"red", "green", "blue", "green"}
print(colors)  # duplicates removed → {'red', 'green', 'blue'}


# In[22]:


# Set operations

a = {1, 2, 3}
b = {3, 4, 5}

print(a | b)  # union → {1, 2, 3, 4, 5}
print(a & b)  # intersection → {3}
print(a - b)  # difference → {1, 2}


# In[15]:


"""
Dictionaries - Key-value pairs
Dictionaries are unordered, mutable, and store pairs:
each value has a unique key.
"""

person = {
    "name": "Alex",
    "age": 35,
    "city": "Dallas"
}


# In[16]:


# Access

print(person["name"])       # Alex
print(person.get("age"))    # 35


# In[17]:


# Modify or add

person["age"] = 36          # update value
person["email"] = "alex@email.com"  # add new key


# In[18]:


# Remove

person.pop("city")
print(person)


# In[19]:


# Loop through dictionary

for key, value in person.items():
    print(f"{key}: {value}")


# In[ ]:


"""
| Type           | Ordered?                            | Changeable? | Allows Duplicates? | Use Case                            |
| -------------- | ----------------------------------- | ----------- | ------------------ | ----------------------------------- |
| **List**       | ✅ Yes                               | ✅ Yes       | ✅ Yes              | Collection of items that can change |
| **Tuple**      | ✅ Yes                               | ❌ No        | ✅ Yes              | Fixed data (e.g., coordinates)      |
| **Set**        | ❌ No                                | ✅ Yes       | ❌ No               | Unique items, set math              |
| **Dictionary** | ❌ (3.7+: maintains insertion order) | ✅ Yes       | ✅ Keys unique      | Key–value data                      |

"""


# In[20]:


# Step 1: Create lists
patients = ["Alice", "Bob", "Charlie"]
ages = [52, 47, 63]

# Step 2: Combine into a dictionary
clinic = {
    "patients": patients,
    "ages": ages
}

# Step 3: Add new patient
clinic["patients"].append("Dana")
clinic["ages"].append(58)

# Step 4: Display info
for name, age in zip(clinic["patients"], clinic["ages"]):
    print(f"{name} is {age} years old.")


# In[ ]:


"""
| Concept    | Example                       |
| ---------- | ----------------------------- |
| List       | `["a", "b", "c"]`             |
| Tuple      | `(1, 2, 3)`                   |
| Set        | `{"a", "b", "c"}`             |
| Dictionary | `{"name": "Alex", "age": 35}` |

"""


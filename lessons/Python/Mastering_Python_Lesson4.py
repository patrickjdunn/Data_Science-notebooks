#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
Now you’re ready to start teaching Python how to think!

Welcome to Lesson 4: Control Flow — if, for, and while statements.

This is one of the most important lessons in becoming a true Python master — because control flow gives your code logic, structure, and intelligence.

Learning Goals

By the end of this lesson, you’ll be able to:
Use if / elif / else to make decisions.
Use for loops to iterate through data.
Use while loops to repeat actions until a condition is met.
Combine logic, comparison, and iteration effectively.

"""


# In[1]:


"""
The if Statement

if lets your program make a decision.
"""

temperature = 102

if temperature > 100:
    print("Fever detected!")


# In[12]:


"""
The colon (:) starts a block, and indentation (4 spaces) defines what belongs to it.

if – elif – else

Python checks conditions in order, and stops at the first that’s true.
"""
bp = 145

if bp < 120:
    print("Normal blood pressure")
elif bp < 130:
    print("Elevated blood pressure")
elif bp < 140:
    print("High blood pressure (Stage 1)")
else:
    print("High blood pressure (Stage 2)")


# In[ ]:


"""
| Operator | Meaning          | Example   | Result |
| -------- | ---------------- | --------- | ------ |
| `==`     | equal to         | `5 == 5`  | True |
| `!=`     | not equal to     | `5 != 3`  | True |
| `>`      | greater than     | `10 > 5`  | True |
| `<`      | less than        | `3 < 9`   | True |
| `>=`     | greater or equal | `8 >= 8`  | True |
| `<=`     | less or equal    | `6 <= 10` | True |

"""


# In[3]:


"""
Combine with and, or, and not:
"""
age = 25
if age > 18 and age < 65:
    print("Adult")


# In[4]:


"""
The for Loop

Loops let you repeat actions — often over items in a collection.

Each loop iteration assigns one value of the list to fruit.

"""
fruits = ["apple", "banana", "cherry"]

for fruit in fruits:
    print(fruit)


# In[5]:


"""
Using range()
range(5) means “start at 0, stop before 5.”

"""
for i in range(5):
    print(i)


# In[6]:


"""
You can also specify start and step:
"""
for i in range(2, 10, 2):
    print(i)  # 2, 4, 6, 8


# In[7]:


"""
Looping with Conditions
"""
for number in range(1, 11):
    if number % 2 == 0:
        print(f"{number} is even")
    else:
        print(f"{number} is odd")


# In[8]:


"""
The while Loop

A while loop runs as long as a condition is true.

Always make sure the condition will eventually become False — or you’ll create an infinite loop.
"""
count = 0

while count < 5:
    print("Count is:", count)
    count += 1


# In[9]:


"""
Break and Continue

break stops the loop entirely.

continue skips to the next iteration.
"""
for i in range(10):
    if i == 5:
        break       # stop loop
    if i % 2 == 0:
        continue    # skip even numbers
    print(i)


# In[10]:


"""
Nested Loops and Conditionals

You can combine loops and if statements:
"""

patients = ["Alice", "Bob", "Charlie"]
bpm = [78, 102, 85]

for i in range(len(patients)):
    if bpm[i] > 100:
        print(f"{patients[i]}: High heart rate!")
    else:
        print(f"{patients[i]}: Normal heart rate.")


# In[11]:


# Daily step tracker
steps = int(input("Enter your step count for today: "))

if steps < 5000:
    print("Let's move more tomorrow!")
elif steps < 10000:
    print("Good job! You’re getting there.")
else:
    print("Excellent work! You’re crushing your goal!")

# Then try replacing input() with a fixed number (e.g., steps = 8200) to test faster.


# In[ ]:


"""
| Concept              | Example             |
| -------------------- | ------------------- |
| `if`                 | `if x > 10:`        |
| `elif` / `else`      | Add more conditions |
| `for` loop           | `for item in list:` |
| `while` loop         | `while condition:`  |
| `break` / `continue` | Control loop flow   |

"""


#!/usr/bin/env python
# coding: utf-8

# In[1]:


"""
You’ve now learned how to make Python think.
Next, let’s make it modular and reusable — this is where your skills start looking professional.

Welcome to Lesson 5: Functions and Scope 

Learning Goals

By the end of this lesson, you’ll be able to:
Define and call functions properly
Use parameters and return values
Understand local vs. global variables (scope)
Write clean, reusable, and modular code

What is a Function?

A function is a reusable block of code that performs a specific task.
It helps you organize, reuse, and test logic easily.
"""

def greet():
    print("Hello! Welcome to Python mastery.")


# In[2]:


# To run it:

greet()


# In[3]:


"""
Parameters and Arguments

You can pass information into functions using parameters:
"""

def greet(name):
    print(f"Hello, {name}!")


# In[4]:


# Call it with an argument:

greet("Alex")


# In[5]:


"""
Returning Values

Use return to send data back from a function.
"""

def add(a, b):
    return a + b

result = add(5, 3)
print(result)  # 8

# A function returns a value that can be stored, printed, or reused.


# In[6]:


# Example: Health Score Function

def health_score(steps, sleep_hours):
    score = steps / 1000 + sleep_hours * 2
    return score

today_score = health_score(8500, 7)
print(f"Your health score today is {today_score:.1f}")


# In[7]:


"""
Default Parameters

You can set default values for parameters.
"""

def greet(name="Friend"):
    print(f"Hello, {name}!")

greet()          # Hello, Friend!
greet("Taylor")  # Hello, Taylor!


# In[8]:


"""
Keyword Arguments

You can specify which argument goes where:
"""

def display_info(name, age, city):
    print(f"{name} is {age} years old and lives in {city}.")

display_info(age=35, name="Alex", city="Dallas")

# This improves clarity, especially with many parameters.


# In[9]:


"""
Variable Scope

Scope = where a variable exists.

Local scope → inside a function

Global scope → outside any function
"""

x = 10  # global variable

def show_value():
    x = 5  # local variable
    print("Inside function:", x)

show_value()
print("Outside function:", x)

# Python treats variables inside functions as local by default.


# In[10]:


# If you want to modify a global variable:

count = 0

def increment():
    global count
    count += 1

increment()
print(count)  # 1


# In[11]:


"""
Multiple Returns

You can return more than one value (as a tuple):
"""

def analyze_numbers(a, b):
    total = a + b
    average = total / 2
    return total, average

sum_result, avg_result = analyze_numbers(8, 12)
print(f"Sum: {sum_result}, Average: {avg_result}")


# In[12]:


# Functions Can Call Other Functions

def square(x):
    return x ** 2

def hypotenuse(a, b):
    return (square(a) + square(b)) ** 0.5

print(hypotenuse(3, 4))  # 5.0

# Functions can build on each other, just like mathematical formulas.


# In[13]:


# Mini Project: Heart Rate Zone Calculator

def target_heart_rate(age, intensity=0.7):
    max_hr = 220 - age
    return max_hr * intensity

age = int(input("Enter your age: "))
zone = target_heart_rate(age, 0.75)
print(f"Your target heart rate at 75% intensity is {zone:.0f} bpm.")

# Try different intensity levels (0.6, 0.85, etc.)


# In[ ]:


"""
| Concept    | Description              | Example                     |
| ---------- | ------------------------ | --------------------------- |
| `def`      | Define a function        | `def greet():`              |
| Parameters | Accept inputs            | `def add(a, b):`            |
| Return     | Send output              | `return a + b`              |
| Default    | Optional parameter value | `def greet(name="Friend"):` |
| Scope      | Variable visibility      | local vs global             |

"""


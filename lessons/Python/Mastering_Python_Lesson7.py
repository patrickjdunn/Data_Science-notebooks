#!/usr/bin/env python
# coding: utf-8

# In[1]:


"""
Welcome to Lesson 7: Object-Oriented Programming (OOP) — one of the most powerful concepts in Python and modern software design.

OOP helps you move from writing small scripts → to building scalable, professional applications (like the Django app you’re developing).

Lesson 7: Object-Oriented Programming (Classes and Objects)
Learning Goals

By the end of this lesson, you’ll be able to:
Understand what classes and objects are
Define classes with attributes and methods
Use constructors (__init__)
Apply principles like encapsulation and inheritance
Build real-world examples

What is Object-Oriented Programming?

OOP is about modeling real-world things in code — objects that have:

Attributes → characteristics or data

Methods → behaviors or actions

Example: A patient in a health system

| Object  | Attributes            | Methods                     |
| ------- | --------------------- | --------------------------- |
| Patient | name, age, heart_rate | record_bp(), show_summary() |

"""

class Patient:
    def __init__(self, name, age):
        self.name = name
        self.age = age


# In[2]:


# Now create an object(instance):

p1 = Patient("Alice", 52)
print(p1.name)
print(p1.age)

"""
__init__ — the Constructor

__init__ runs automatically when you create an object.

It initializes its attributes.
"""


# In[3]:


"""
Adding Methods

Methods are functions inside classes.
"""

class Patient:
    def __init__(self, name, age, heart_rate):
        self.name = name
        self.age = age
        self.heart_rate = heart_rate

    def display_info(self):
        print(f"{self.name} is {self.age} years old with a heart rate of {self.heart_rate} bpm.")


# In[4]:


# Create and call the method:

p1 = Patient("Bob", 47, 88)
p1.display_info()


# In[5]:


"""
Modifying Object Attributes

You can change attributes like this:
"""

p1.heart_rate = 75
p1.display_info()


# In[6]:


"""
Encapsulation — Protecting Data

Prefix an attribute with _ to indicate it’s “private” (by convention).
"""

class Patient:
    def __init__(self, name, age):
        self._name = name
        self._age = age

    def get_age(self):
        return self._age

    def set_age(self, new_age):
        if new_age > 0:
            self._age = new_age
        else:
            print("Invalid age.")


# In[7]:


# Use

p = Patient("Alice", 52)
print(p.get_age())
p.set_age(53)


# In[8]:


"""
Inheritance — Building on Existing Classes

You can create new classes that extend existing ones.
"""

class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def speak(self):
        print(f"{self.name} says hello!")

class Patient(Person):
    def __init__(self, name, age, condition):
        super().__init__(name, age)  # call parent constructor
        self.condition = condition

    def show_condition(self):
        print(f"{self.name} is being treated for {self.condition}.")


# In[9]:


# Use it

p = Patient("Charlie", 63, "Hypertension")
p.speak()
p.show_condition()


# In[10]:


# Class vs instance variables

class Patient:
    hospital = "HeartCare Center"   # class variable

    def __init__(self, name):
        self.name = name            # instance variable
        
# Each object shares hospital, but has its own name.


# In[11]:


p1 = Patient("Alice")
p2 = Patient("Bob")

print(p1.hospital, p1.name)
print(p2.hospital, p2.name)


# In[12]:


"""
Dunder (“Double Underscore”) Methods

You can make your objects act like built-ins.
"""

class Patient:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __str__(self):
        return f"Patient {self.name}, age {self.age}"


# In[13]:


# Now printing the object gives:

p = Patient("Dana", 58)
print(p)


# In[14]:


# Mini Project: Blood Pressure Tracker

class BloodPressure:
    def __init__(self, systolic, diastolic):
        self.systolic = systolic
        self.diastolic = diastolic

    def category(self):
        if self.systolic < 120 and self.diastolic < 80:
            return "Normal"
        elif self.systolic < 130:
            return "Elevated"
        elif self.systolic < 140 or self.diastolic < 90:
            return "Hypertension (Stage 1)"
        else:
            return "Hypertension (Stage 2)"

bp1 = BloodPressure(138, 85)
print(f"BP Category: {bp1.category()}")


# In[ ]:


"""
| Concept     | Description           | Example                   |
| ----------- | --------------------- | ------------------------- |
| Class       | Blueprint for objects | `class Patient:`          |
| Object      | Instance of a class   | `p1 = Patient()`          |
| Attribute   | Variable in a class   | `self.name`               |
| Method      | Function in a class   | `def display_info(self):` |
| Inheritance | Extend a class        | `class Child(Parent):`    |

"""


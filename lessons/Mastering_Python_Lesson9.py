#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
Lesson 9: Error Handling and Debugging
🎯 Learning Goals

By the end of this lesson, you’ll be able to:

Understand different types of errors and exceptions

Handle them using try, except, else, and finally

Raise your own custom exceptions

Use debugging tools (like Spyder’s debugger and breakpoints)

Write more reliable and fault-tolerant code

What Are Errors?

There are two main types:

| Type             | Description               | Example                      |
| ---------------- | ------------------------- | ---------------------------- |
| **Syntax Error** | Mistake in code structure | `print("hello"`              |
| **Exception**    | Error *during execution*  | `10 / 0` (ZeroDivisionError) |

"""


# In[1]:


print("Before error")
print(10 / 0)  # causes ZeroDivisionError
print("After error")

# The program stops when it hits an exception


# In[2]:


"""
Handling Exceptions with try–except

We can prevent crashes by “catching” exceptions:
"""

try:
    x = 10 / 0
except ZeroDivisionError:
    print("You can’t divide by zero!")

# The program continues running.


# In[3]:


# Multiple except Blocks

try:
    num = int(input("Enter a number: "))
    result = 10 / num
    print(result)
except ZeroDivisionError:
    print("You can’t divide by zero.")
except ValueError:
    print("That’s not a valid number.")


# In[4]:


# Catch all exceptions, to handle any kind of error:

try:
    risky_operation()
except Exception as e:
    print("Error:", e)


# In[5]:


# The Full try-except-else-finally structure

try:
    num = int(input("Enter a number: "))
    result = 10 / num
except ZeroDivisionError:
    print("Cannot divide by zero.")
except ValueError:
    print("Please enter a valid number.")
else:
    print("Success! Result =", result)
finally:
    print("Operation complete.")

"""
Flow:

try: code to attempt

except: what to do if it fails

else: runs only if no error occurred

finally: runs no matter what (cleanup, closing files, etc.)
"""


# In[6]:


"""
Raising Your Own Exceptions

You can intentionally raise an error when something invalid happens.
"""

def check_heart_rate(bpm):
    if bpm <= 0:
        raise ValueError("Heart rate must be positive.")
    elif bpm < 100:
        return "Normal"
    else:
        return "Tachycardia"

try:
    print(check_heart_rate(-80))
except ValueError as e:
    print("Error:", e)



# In[7]:


"""
Custom Exception Classes

You can create your own exception type:
"""

class HeartRateError(Exception):
    pass

def analyze_hr(bpm):
    if bpm < 30 or bpm > 200:
        raise HeartRateError("Abnormal heart rate detected.")
    return "Heart rate is within normal range."

try:
    print(analyze_hr(220))
except HeartRateError as e:
    print(e)


# In[8]:


def calculate_bmi(weight, height):
    try:
        bmi = weight / (height ** 2)
        return round(bmi, 1)
    except TypeError:
        print("Please use numbers for weight and height.")
    except ZeroDivisionError:
        print("Height cannot be zero.")
    else:
        print("BMI calculation successful.")
    finally:
        print("Function complete.")

print(calculate_bmi(70, 1.75))
print(calculate_bmi("seventy", 1.75))


# In[ ]:


"""
| Concept   | Description               | Example                       |
| --------- | ------------------------- | ----------------------------- |
| `try`     | Attempt a risky operation | `try: x = 10 / 0`             |
| `except`  | Handle specific error     | `except ZeroDivisionError:`   |
| `else`    | Runs if no error          | `else: print("Success!")`     |
| `finally` | Always runs               | `finally: print("Done")`      |
| `raise`   | Trigger custom error      | `raise ValueError("Invalid")` |

Pro Tips

Catch only specific exceptions when possible.
Use finally for cleanup (closing files, database connections, etc.).
Don’t silence all exceptions with a blank except: — it hides bugs.
Use the Spyder debugger to inspect logic and variable state.
"""


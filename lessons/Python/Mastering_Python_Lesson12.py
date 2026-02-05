#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Example: Health-Style API (Simulated)
# Let's simulate a health API that returns heart rate, steps, and sleep data

import requests
import pandas as pd

# pretend API
url = "https://api.example.com/healthdata"  # hypothetical
response = {
    "user": "Alex",
    "data": [
        {"date": "2025-10-21", "heart_rate": 78, "steps": 8500, "sleep": 7.0},
        {"date": "2025-10-22", "heart_rate": 82, "steps": 9100, "sleep": 6.5},
        {"date": "2025-10-23", "heart_rate": 76, "steps": 10400, "sleep": 7.8},
    ]
}

df = pd.DataFrame(response["data"])
print(df)


# In[2]:


# Visualize API Data

import matplotlib.pyplot as plt

plt.plot(df["date"], df["heart_rate"], marker="o", label="Heart Rate (bpm)")
plt.plot(df["date"], df["steps"], marker="s", label="Steps")
plt.title("Heart Rate and Steps Over Time")
plt.xlabel("Date")
plt.legend()
plt.grid(True)
plt.show()

# This combines real-world API data with pandas + matplotlib visualization


# In[3]:


# Handling API Errors Gracefully
# always use error handling when calling APIs

try:
    response = requests.get(url)
    response.raise_for_status()  # raises HTTPError if not 200
    data = response.json()
except requests.exceptions.RequestException as e:
    print("API error:", e)

"""
| Concept            | Description               | Example                       |
| ------------------ | ------------------------- | ----------------------------- |
| `requests.get()`   | Send HTTP GET request     | `requests.get(url)`           |
| `.json()`          | Parse JSON response       | `data = response.json()`      |
| API key            | Authentication credential | `?appid=YOUR_KEY`             |
| pandas integration | Analyze API data          | `pd.DataFrame(data)`          |
| Error handling     | Manage bad responses      | `response.raise_for_status()` |

"""


# In[ ]:





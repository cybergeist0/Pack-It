import requests
import google.generativeai as genai
import os

# Load API keys from key.txt
with open("key.txt", "r") as file:
    keys = file.readlines()
    GENERATIVE_API_KEY = keys[0].strip()   # First line for Generative API key
    SEARCH_API_KEY = keys[1].strip()       # Second line for Google Search API key
    SEARCH_ENGINE_ID = keys[2].strip()     # Third line for Search Engine ID

# Configure the generative AI model with the provided API key
genai.configure(api_key=GENERATIVE_API_KEY)

def test_google_search_api(query):
    """Test the Google Search API by retrieving a snippet for a query."""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": SEARCH_API_KEY,
        "cx": SEARCH_ENGINE_ID
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "items" in data:
        snippet = data["items"][0]["snippet"]
        print("Google Search API Test:")
        print(f"Snippet for '{query}':\n{snippet}\n")
        return snippet
    else:
        print("Google Search API Test Failed: No results found.")
        print("Response received:", data)  # Print the entire response for debugging
        return None

def test_generative_ai_api(snippet):
    """Test the Generative AI API by summarizing the search snippet."""
    if not snippet:
        print("No snippet provided for summarization.")
        return

    prompt = (
        "Please summarize the following information:\n\n"
        f"{snippet}\n\n"
    )
    
    model = genai.GenerativeModel("gemini-1.5-flash")  # Internally configured
    response = model.generate_content(prompt)

    print("Generative Language API Test:")
    print("Summary:")
    print(response.text)

# Run tests
query = "Artificial Intelligence applications"
print("Testing APIs...\n")

snippet = test_google_search_api(query)
if snippet:
    test_generative_ai_api(snippet)

print("\nAPI tests completed.")

import requests
import json

def test_lm_studio():
    """Test the LM Studio API connection and functionality"""
    api_url = "http://127.0.0.1:1234/v1/chat/completions"
    
    # Simple test prompt
    payload = {
        "model": "mistral-nemo-instruct-2407",  # Make sure this model is loaded in LM Studio
        "messages": [{"role": "user", "content": "Hello, are you there?"}],
        "max_tokens": 100
    }
    
    try:
        print("Sending request to LM Studio...")
        response = requests.post(api_url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("\nConnection successful!\n")
            print("Response from LM Studio:")
            print(result["choices"][0]["message"]["content"])
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Connection error: {str(e)}")
        print("\nMake sure LM Studio is running and the model is loaded.")
        print("The API should be accessible at http://127.0.0.1:1234")

if __name__ == "__main__":
    test_lm_studio()
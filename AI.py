import os
# Update the import to the non-deprecated class
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the OpenAI API key from the environment variable
key = os.environ.get("OPENAI_API_KEY")

# Initialize the OpenAI model
llm = ChatOpenAI(temperature=0.9, openai_api_key=key, model_name="gpt-3.5-turbo-0613")

# Function to read text from a local file
def read_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

text_file_path = input("Enter the path of your text file: ")
user_prompt = input("Enter your prompt: ")

def split_text_into_chunks(text, chunk_size):
    """Splits the text into smaller chunks each of roughly chunk_size characters.

    Args:
    text (str): The original text.
    chunk_size (int): The maximum size of each chunk in characters.

    Returns:
    list: A list of text chunks.
    """
    chunks = []
    while text:
        # Take the first `chunk_size` characters from the text
        chunk = text[:chunk_size]
        print(chunk)
        print("--------------------------------\n")
        chunks.append(chunk)

        # Remove the processed part from the text
        text = text[chunk_size:]

    return chunks

# Usage
text = read_text_from_file(text_file_path)
chunks = split_text_into_chunks(text, 4000)  # Adjust chunk_size as needed

responses = []
for chunk in chunks:
    combined_input = chunk + "\n\n" + user_prompt
    response = llm.invoke(combined_input)
    responses.append(str(response))
    print(response)

combined_responses = ''.join(responses)

combined_input = combined_responses + "\n\n" + user_prompt

# Get the response from the language model
response = llm.invoke(combined_input)

# Print the response
print("SUMMARY:\n")
print(response)
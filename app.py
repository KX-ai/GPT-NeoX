import os
import openai
import PyPDF2
import streamlit as st

# Use the Sambanova API for Qwen 2.5-72B-Instruct
class SambanovaClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        openai.api_key = self.api_key  # Set the API key for the OpenAI client
        openai.api_base = self.base_url  # Set the base URL for the OpenAI API

    def chat(self, model, messages, temperature=0.7, top_p=1.0, max_tokens=500):
        try:
            # Increased max_tokens for longer responses
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,  # Allowing for longer responses
                top_p=top_p
            )
            return response
        except Exception as e:
            raise Exception(f"Error while calling OpenAI API: {str(e)}")

# Function to extract text from PDF using PyPDF2
def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Streamlit UI
st.title("Chatbot with PDF Content")
st.write("Upload a PDF file and ask questions about its content.")

# File upload
pdf_file = st.file_uploader("Upload your PDF file", type="pdf")

if pdf_file is not None:
    # Extract text from the uploaded PDF
    text_content = extract_text_from_pdf(pdf_file)
    st.write("PDF content extracted successfully.")

    # Retrieve the API key securely from Streamlit Secrets
    api_key = st.secrets["general"]["SAMBANOVA_API_KEY"]
    if not api_key:
        st.error("API key not found! Please check your secrets settings.")
    else:
        sambanova_client = SambanovaClient(
            api_key=api_key,
            base_url="https://api.sambanova.ai/v1"
        )

        # Initialize session_state to store chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [{"role": "system", "content": "You are a helpful assistant"}]
        
        # Chat functionality
        user_input = st.text_input("Ask a question about the document:")

        if user_input:
            # Add user input to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            # Create prompt for Qwen 2.5 Instruct model using the extracted text (limit size)
            # We limit the text size for better performance with token limits
            prompt_text = f"Document content (truncated): {text_content[:1000]}...\n\nUser question: {user_input}\nAnswer:"

            # Add prompt text to the chat history
            st.session_state.chat_history.append({"role": "system", "content": prompt_text})

            try:
                # Call the Qwen2.5-72B-Instruct model to generate a response
                response = sambanova_client.chat(
                    model="Qwen2.5-72B-Instruct",  # Model name
                    messages=st.session_state.chat_history,
                    temperature=0.1,
                    top_p=0.1,
                    max_tokens=500  # Allowing longer responses
                )

                # Get and display the response from the model
                answer = response['choices'][0]['message']['content'].strip()  # Correct access to response
                st.write(f"Qwen 2.5: {answer}")

                # Add model response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": answer})

            except Exception as e:
                st.error(f"Error occurred while fetching response: {str(e)}")

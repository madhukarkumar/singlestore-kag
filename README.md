# Project Setup

This project uses Python with the following dependencies:

- requests
- openai
- python-dotenv
- PyPDF2

## Setting Up a Virtual Environment Using pyenv

1. **Install pyenv** (if not already installed):
   Follow the instructions on the [pyenv GitHub page](https://github.com/pyenv/pyenv) for your operating system.

2. **Install the Latest Python Version**
   You can install the latest stable version of Python (for example, 3.11.4) using pyenv:
   
   ```bash
   pyenv install 3.12.9
   ```

3. **Create a Virtual Environment**
   Create a new virtual environment using the installed version. You can use pyenv-virtualenv for this. For example:
   
   ```bash
   pyenv virtualenv 3.12.9 myenv
   ```
{{ ... }}
# Before reading the PDF file
print("DEBUG: Starting processing of PDF file:", pdf_path)
logger.info("Reading PDF file: %s", pdf_path)
{{ ... }}
# After reading the PDF file and before calling the API
print("DEBUG: Finished reading PDF file. Preparing to call Gemini API.")
{{ ... }}
try:
    # Log payload details before making the call
    print("DEBUG: Calling Gemini Flash LLM API with payload:", payload)
    logger.info("Calling Gemini Flash LLM API...")
    response = requests.post(api_url, json=payload)
    print("DEBUG: Received response with status code:", response.status_code)
    response.raise_for_status()
    {{ ... }}  # Process the successful response here.
except requests.exceptions.HTTPError as http_err:
    error_message = f"HTTP error occurred: {http_err} - Response: {response.text}"
    print("DEBUG:", error_message)
    logger.error("Error calling Gemini API: %s", error_message)
    {{ ... }}
except Exception as err:
    print("DEBUG: An unexpected error occurred:", err)
    logger.error("Processing failed: %s", err)
    {{ ... }}
{{ ... }}
# At the end of the process
print("DEBUG: Ending main execution.")
{{ ... }}{{ ... }}
# Before reading the PDF file
print("DEBUG: Starting processing of PDF file:", pdf_path)
logger.info("Reading PDF file: %s", pdf_path)
{{ ... }}
# After reading the PDF file and before calling the API
print("DEBUG: Finished reading PDF file. Preparing to call Gemini API.")
{{ ... }}
try:
    # Log payload details before making the call
    print("DEBUG: Calling Gemini Flash LLM API with payload:", payload)
    logger.info("Calling Gemini Flash LLM API...")
    response = requests.post(api_url, json=payload)
    print("DEBUG: Received response with status code:", response.status_code)
    response.raise_for_status()
    {{ ... }}  # Process the successful response here.
except requests.exceptions.HTTPError as http_err:
    error_message = f"HTTP error occurred: {http_err} - Response: {response.text}"
    print("DEBUG:", error_message)
    logger.error("Error calling Gemini API: %s", error_message)
    {{ ... }}
except Exception as err:
    print("DEBUG: An unexpected error occurred:", err)
    logger.error("Processing failed: %s", err)
    {{ ... }}
{{ ... }}
# At the end of the process
print("DEBUG: Ending main execution.")
{{ ... }}
4. **Activate the Virtual Environment**
   Activate your virtual environment:
   
   ```bash
   pyenv activate myenv
   ```

5. **Install Project Dependencies**
   Once your virtual environment is active, install the required packages:
   
   ```bash
   pip install -r requirements.txt
   ```

6. **Running the Application**
   To run the application, place your PDF files in the `documents` folder and then run:
   
   ```bash
   python main.py your_file.pdf
   ```

   To run only the get_chunks function and inspect the generated markdown file, use:
   
   ```bash
   python main.py your_file.pdf --get-chunks-only
   ```

Happy coding!

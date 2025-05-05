import PyPDF2

def convert_pdf_to_text(pdf_path, text_path):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        with open(text_path, 'w', encoding='utf-8') as text_file:
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text_file.write(page.extract_text())

import os
import time
def replace_continue_with_empty_line(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    updated_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == 'continue...' and i + 2 < len(lines) and lines[i + 3].strip() == 'Out of Control':
            updated_lines.append('\n')
            i += 4
        else:
            updated_lines.append(lines[i])
            i += 1

    base_name, extension = os.path.splitext(file_path)
    new_file_path = f"{base_name}1{extension}"
    with open(new_file_path, 'w', encoding='utf-8') as file:
        file.writelines(updated_lines)

    return new_file_path

def remove_duplicate_chapters(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    chapter_titles = set()
    updated_lines = []
    for line in lines:
        if "Chapter" in line and ":" in line:
            chapter_title = line.strip()
            if chapter_title not in chapter_titles:
                updated_lines.append(line)
                chapter_titles.add(chapter_title)
        else:
            updated_lines.append(line)

    base_name, extension = os.path.splitext(file_path)
    new_file_path = f"{base_name}_processed{extension}"
    with open(new_file_path, 'w', encoding='utf-8') as file:
        file.writelines(updated_lines)

    return new_file_path


import openai
import time

def summarize_text(text, divider=1, model_name='gpt-3.5-turbo'):
    # Calculate target summary size based on text size and divider
    text_size = len(text)
    target_size = text_size // divider

    # Divide text into sentences
    sentences = text.split('. ')
    
    # Accumulate sentences into chunks of maximum size 4096 tokens
    chunks = []
    current_chunk = ''
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 2 <= 4096:  # Add 2 for the period and space after each sentence
            current_chunk += sentence + '. '
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + '. '
    if current_chunk:
        chunks.append(current_chunk.strip())

    # Calculate summary size for each chunk
    summary_size = min(target_size // len(chunks), 4096)

    # Summarize each chunk using the OpenAI API
    summarized_chunks = []
    for chunk in chunks:
        response = None
        while response is None:
            try:
                response = openai.ChatCompletion.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": f"Please summarize the text I'll paste, write it all in russian, providing a concise summary of the main points and understandings. Aim for clarity and coherence in your summary. You may also identify key arguments or evidence, provide analysis or critical evaluation, and offer insights or comparisons. Please keep the summary within {summary_size} tokens."},
                        {"role": "user", "content": chunk}
                    ],
                    max_tokens=summary_size,
                    temperature=0.5,
                    n=1,
                    stop=None
                )
                summarized_text = response.choices[0].message['content']
                summarized_chunks.append(summarized_text)
            except openai.error.RateLimitError as e:
                print("Rate limit reached. Waiting for 20 seconds...")
                time.sleep(20)
                continue
            except openai.error.OpenAIError as e:
                # Handle other API errors as needed
                print(f"API Error: {e}")
    
    # Return the summarized text
    summarized_text = ' '.join(summarized_chunks)
    return summarized_text



import os
import re

def create_chapter_files(file_name):
    # Create a folder with the specified file name
    folder_name = os.path.splitext(file_name)[0]
    os.makedirs(folder_name, exist_ok=True)

    # Read the contents of the file
    with open(file_name, 'r', encoding='utf-8') as file:
        content = file.read()

    # Split the text into chapters using regular expressions
    chapters = re.split(r'(?<!\S)Chapter\s+\d+\s*:', content)

    # Remove any leading/trailing whitespace from each chapter
    chapters = [chapter.strip() for chapter in chapters if chapter.strip()]

    # Write each chapter to a separate file
    for i, chapter in enumerate(chapters):
        chapter_file_name = f"{folder_name}/Chapter_{i+1}.txt"
        with open(chapter_file_name, 'w', encoding='utf-8') as chapter_file:
            chapter_file.write(chapter)

    print("Chapter files created successfully.")


from openai import OpenAIError

def summarize_chapters_in_folder(chapters_folder, divider):
    # Create a new folder for the summarized chapters
    output_folder = f"{chapters_folder}_div{divider}"
    os.makedirs(output_folder, exist_ok=True)

    # Get the list of chapter files in the folder
    chapter_files = [f for f in os.listdir(chapters_folder) if os.path.isfile(os.path.join(chapters_folder, f))]

    # Sort the chapter files by their numerical order
    chapter_files.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))

    # Initialize a counter for the number of requests made
    requests_count = 0

    # Summarize each chapter and save the summarized content
    for chapter_file in chapter_files:
        chapter_path = os.path.join(chapters_folder, chapter_file)
        with open(chapter_path, 'r', encoding='utf-8') as file:
            chapter_text = file.read()

        # Extract the chapter number from the file name
        chapter_number = chapter_file.split("_")[1].split(".")[0]


        # Summarize the chapter text
        summarized_text = summarize_text(chapter_text, divider)

        # Create the output file name for the summarized chapter
        output_file = f"Chapter_{chapter_number}_Summary.txt"
        output_file_path = os.path.join(output_folder, output_file)

        # Save the summarized chapter content to the output file
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(summarized_text)

        time.sleep(21)




def combine_chapters_in_folder(folder_name):
    # Get the list of chapter files in the folder
    chapter_files = [f for f in os.listdir(folder_name) if os.path.isfile(os.path.join(folder_name, f))]

    # Sort the chapter files by their numerical order
    chapter_files.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))

    # Initialize a list to store the combined chapters
    combined_chapters = []

    # Combine the content of each chapter
    for chapter_file in chapter_files:
        chapter_path = os.path.join(folder_name, chapter_file)
        with open(chapter_path, 'r', encoding='utf-8') as file:
            chapter_text = file.read()

        # Extract the chapter number from the file name
        chapter_number = chapter_file.split("_")[1].split(".")[0]

        # Add the chapter header and content to the combined chapters
        chapter_header = f"Chapter {chapter_number}:"
        combined_chapters.append(f"{chapter_header}\n{chapter_text}")

    # Create the combined book file name
    combined_book_file_name = f"{folder_name}_CombinedBook.txt"
    combined_book_file_path = os.path.join(os.path.dirname(folder_name), combined_book_file_name)

    # Write the combined chapters to the combined book file
    with open(combined_book_file_path, 'w', encoding='utf-8') as combined_book_file:
        combined_book_file.write('\n\n'.join(combined_chapters))

    print("Combined book file created successfully.")





openai.api_key = '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'
# Example usage
pdf_path = 'ksenia job.pdf'
text_path = 'ksenia job.txt'
#convert_pdf_to_text(pdf_path, text_path)
#replace_continue_with_empty_line(text_path)
#remove_duplicate_chapters(text_path)
with open(text_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()
    text = ' '.join(line.strip() for line in lines)
summarized_text = summarize_text(text,4)
with open("ksenia_summary.txt", 'w', encoding='utf-8') as output_file:
    output_file.write(summarized_text)
# Usage example
#file_name = "book.txt"
#create_chapter_files(text_path)
#folder_name = "perseus_books.out_of_control1_processed_div4" #os.path.splitext(text_path)[0]
#summarize_chapters_in_folder(folder_name,4)
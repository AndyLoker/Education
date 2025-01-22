import time
import traceback
import openai
from talker import talk
from tags import process_tags

import APIkey
openai.api_key = APIkey.OpenAI
assistant_id = APIkey.AssistantId

my_thread_id = None  # store the current thread ID globally

def process_user_input(user_input):
    """
    Sends user input to the assistant, waits for a response,
    speaks it, and processes any tags (including dispensing).
    """
    global my_thread_id

    if user_input.lower() == "quit":
        print("Exiting program.")
        exit()

    # Ensure there's a thread
    if my_thread_id is None:
        thread = openai.beta.threads.create()
        my_thread_id = thread.id

    # Create the message, run it, then poll until completion
    my_run_id, my_thread_id = load_thread(assistant_id, user_input, my_thread_id)
    status = check_status(my_run_id, my_thread_id)

    while status != "completed":
        time.sleep(2)
        status = check_status(my_run_id, my_thread_id)

    # Retrieve the response
    response = openai.beta.threads.messages.list(thread_id=my_thread_id)
    if response.data:
        # Get the assistant's text
        answer = response.data[0].content[0].text.value

        # Print raw
        print("RAW RESPONSE:", answer)
        # Clean up tags for TTS output
        cleaned_answer = remove_tags(answer)
        print("TTS OUTPUT:", cleaned_answer)
        talk(cleaned_answer)

        # Process tags (which may trigger motor commands on the Pico)
        process_tags(answer)

        # If the assistant says @goodbye, create a new thread
        if "@goodbye" in answer:
            print("Assistant indicated to end the conversation. Starting new thread.")
            new_thread = openai.beta.threads.create()
            my_thread_id = new_thread.id
    else:
        print("No response from assistant.")

def load_thread(ass_id, prompt, thread_id):
    # Send the user's message
    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=prompt
    )
    # Create a run
    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ass_id,
    )
    return run.id, thread_id

def check_status(run_id, thread_id):
    run = openai.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id,
    )
    return run.status

def remove_tags(text):
    """
    Removes known tags from the text so the spoken output is clean.
    """
    # E.g., remove @10, @11, etc., plus @goodbye or any other special tags
    tags_to_remove = ["@10", "@11", "@12", "@13", "@14", "@15", "@16", "@17", "@18", "@19", "@goodbye"]
    for tag in tags_to_remove:
        text = text.replace(tag, "")
    # You could also remove any bracketed info or other custom tags if needed
    return " ".join(text.split())

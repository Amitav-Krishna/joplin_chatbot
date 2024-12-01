import os 
import argparse 
from joppy.client_api import ClientApi
from openai import OpenAI
import re

JOPLIN_TOKEN = os.getenv("JOPLIN_TOKEN")
joplin = ClientApi(token=JOPLIN_TOKEN)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def fetch_all_notes():    
    try:
        all_notes = []
        page = 1
        while True:
            notes = joplin.get_notes(page=page, limit=100, fields="id,title,body")
            if not notes.items:
                break
            all_notes.extend([f"Title: {note.title}\nContent: {note.body}" for note in notes.items])
            page += 1
        print(f"Fetched {len(all_notes)} notes.")
        return all_notes
    except Exception as e:
        print(f"Error fetching notes: {e}")        
        return None

def normalize_text(text):
    # Remove non-alphanumeric characters and normalize whitespace
    return re.sub(r'\W+', ' ', text).strip().lower()
def filter_relevant_notes(notes, query):
    relevant_notes = []
    normalized_query = normalize_text(query)
    query_keywords = normalized_query.split()
    
    for note in notes:
        note_content = normalize_text(note)
        relevance_score = sum(keyword in note_content for keyword in query_keywords)
        if relevance_score > 0:
            relevant_notes.append((note, relevance_score))
    
    relevant_notes.sort(key=lambda x: x[1], reverse=True)
    print(f"Found {len(relevant_notes)} relevant notes.")
    return [note for note, _ in relevant_notes[:10]]  # Return top 10 most relevant notes

def ask_gpt(client, question, notes_context):
    try:        
        response = client.chat.completions.create(             
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that summarizes information from notes. Focus only on the content provided in the notes."},
                {"role": "user", "content": f"Based on the following notes, summarize the key points to answer this question: {question}\n\nNotes:\n{notes_context}"}
            ]        
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error querying GPT: {e}")         
        return None

def main():     
    parser = argparse.ArgumentParser(description="Query Joplin notes and get answers.")    
    parser.add_argument("question", type=str, help="The question you want to ask about your notes")    
    args = parser.parse_args()     

    print(f"Question: {args.question}")

    all_notes = fetch_all_notes()
    if not all_notes:
        print("Could not fetch notes. Exiting.")
        return

    relevant_notes = filter_relevant_notes(all_notes, args.question)
    
    if not relevant_notes:
        print("Could not find relevant notes. Exiting.")
        return

    # Summarize the relevant notes before sending to GPT
#    limited_notes_context = summarize_relevant_notes(relevant_notes)

    # Check token count and limit if necessary
    token_limit = 4096  # Adjust based on model used (4096 for gpt-3.5-turbo)
    
    # Count tokens (simple approximation)
    #estimated_tokens = len(limited_notes_context.split())
    

    print("Sending query to GPT...")
    answer = ask_gpt(client, args.question, relevant_notes)     
    if answer:         
        print("\n--- Answer ---\n")         
        print(answer)     
    else:         
        print("Could not generate an answer. Exiting.") 

if __name__ == "__main__":     
    main()


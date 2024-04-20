import streamlit as st
import requests
import json
import time
import pprint
from api_secrets import API_KEY_ASSEMBLYAI, API_KEY_LISTENNOTES

transcript_endpoint = 'https://api.assemblyai.com/v2/transcript'
listennotes_episode_endpoint = 'https://listen-api.listennotes.com/api/v2/episodes'

headers_assemblyai = {
    'Authorization': f'API_KEY {API_KEY_ASSEMBLYAI}',
    'Content-Type': 'application/json'
}

headers_listennotes = {
    'X-ListenAPI-Key': API_KEY_LISTENNOTES,
}

def fetch_data_from_api(episode_id):
    response = requests.get(f"{listennotes_episode_endpoint}/{episode_id}", headers=headers_listennotes)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching episode data for episode ID {episode_id}: {response.text}")
        return None

def get_episode_audio_url(episode_id):
    data = fetch_data_from_api(episode_id)
    
    if data is None:
        st.error("Error: Unable to fetch data from API")
        return None, None, None, None
    
    if 'podcast' in data:
        podcast_title = data['podcast'].get('title', 'Unknown Podcast Title')
        episode_title = data.get('title', 'Unknown Episode Title')
    else:
        podcast_title = "Unknown Podcast Title"
        episode_title = "Unknown Episode Title"
    
    audio_url = data.get('audio', '')
    thumbnail = data.get('image', '')
    
    return audio_url, thumbnail, podcast_title, episode_title


def transcribe(audio_url, auto_chapters):
    transcript_request = {
        'audio_url': audio_url,
        'auto_chapters': auto_chapters
    }
    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers_assemblyai)

    if transcript_response.status_code == 201 or transcript_response.status_code == 200: 
        transcript_id = transcript_response.json()['id']
        return transcript_id
    else:
        st.error(f"Error: {transcript_response.text}")
        return None

def poll(transcript_id):
    polling_endpoint = f"{transcript_endpoint}/{transcript_id}"
    polling_response = requests.get(polling_endpoint, headers=headers_assemblyai)
    return polling_response.json()

def get_transcription_result_url(url, auto_chapters):
    transcribe_id = transcribe(url, auto_chapters)
    if transcribe_id:
        while True:
            data = poll(transcribe_id)
            if data.get('status') == 'completed':
                return data, None
            elif data.get('status') == 'error':
                return data, data['error']
            msgs("Wait I'm working on it!!", type = 2)
    else:
        return None, "Transcription failed"

def save_transcript(episode_id):
    audio_url, thumbnail, podcast_title, episode_title = get_episode_audio_url(episode_id)
    
    data, error = get_transcription_result_url(audio_url, auto_chapters=True)
    if data:
        try:
            filename_text = f"{episode_id}.txt"
            with open(filename_text, 'w') as f:
                f.write(data['text'])
                msgs(f"Text transcript saved to:{filename_text}", type = 1)
            
            filename_json = f"{episode_id}_chapters.json"
            with open(filename_json, 'w') as f:
                chapters = data['chapters']
                data_to_save = {
                    'chapters': chapters,
                    'audio_url': audio_url,
                    'thumbnail': thumbnail,
                    'podcast_title': podcast_title,
                    'episode_title': episode_title
                }
                json.dump(data_to_save, f, indent=4)
                msgs(f"JSON transcript saved to:{filename_json}", type = 1)
            return True
        except Exception as e:
            msgs(f"Error occurred while saving transcript:{str(e)}")
            return False
    
    elif error:
        st.error("Error:", error)
        return False
def msgs(msg, type = 0):
    sp = st.empty()
    sp.success(f"{msg}") if type == 1 else sp.info(f"{msg}") if type == 2 else sp.error(f"{msg}")
    time.sleep(60) if type == 2 else time.sleep(5) 
    sp.empty()
if __name__ == "__main__":
    st.title("Episode Transcription")

    episode_id = st.sidebar.text_input("Enter Episode ID")
    if episode_id:
        st.info("Processing...")
        save_transcript(episode_id)

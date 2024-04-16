import requests
import json
import time
import pprint
from api_secrets import API_KEY_ASSEMBLYAI, API_KEY_LISTENNOTES

transcript_endpoint = 'https://api.assemblyai.com/v2/transcript'
listennotes_episode_endpoint = 'https://listen-api.listennotes.com/api/v2/episodes'

headers_assemblyai = {
    "authorization": API_KEY_ASSEMBLYAI,
    "content-type": "application/json"
}

headers_listennotes = {
    'X-ListenAPI-Key': API_KEY_LISTENNOTES,
}

def fetch_data_from_api(episode_id):
    # Placeholder for actual API call
    pass

def get_episode_audio_url(episode_id):
    data = fetch_data_from_api(episode_id)
    
    if data is None:
        print("Error: Unable to fetch data from API")
        return None, None, None, None
    
    if 'podcast' in data:
        podcast_title = data['podcast'].get('episode_title', 'Unknown Episode Title')
        episode_title = data.get('title', 'Unknown Title')
    else:
        podcast_title = "Unknown Episode Title"
        episode_title = "Unknown Title"
    
    audio_url = data.get('audio_url', '')
    thumbnail = data.get('thumbnail', '')
    
    return audio_url, thumbnail, podcast_title, episode_title


def transcribe(audio_url, auto_chapters):
    transcript_request = {
        'audio_url': audio_url,
        'auto_chapters': auto_chapters
    }

    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers_assemblyai)
    if transcript_response.status_code == 201:
        transcript_id = transcript_response.json()['id']
        return transcript_id
    else:
        print("Error:", transcript_response.text)
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

            print("Waiting for 60 seconds")
            time.sleep(60)
    else:
        return None, "Transcription failed"

def save_transcript(episode_id):
    audio_url, thumbnail, podcast_title, episode_title = get_episode_audio_url(episode_id)
    data, error = get_transcription_result_url(audio_url, auto_chapters=True)
    if data:
        filename = f"{episode_id}.txt"
        with open(filename, 'w') as f:
            f.write(data['text'])

        filename = f"{episode_id}_chapters.json"
        with open(filename, 'w') as f:
            chapters = data['chapters']
            data_to_save = {
                'chapters': chapters,
                'audio_url': audio_url,
                'thumbnail': thumbnail,
                'podcast_title': podcast_title,
                'episode_title': episode_title
            }
            json.dump(data_to_save, f, indent=4)
            print('Transcript saved')
            return True
    elif error:
        print("Error:", error)
        return False

if __name__ == "__main__":
    episode_id = "your_episode_id_here"
    save_transcript(episode_id)

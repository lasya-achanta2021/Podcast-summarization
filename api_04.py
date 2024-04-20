import requests
import json
import time
import pprint
from api_secrets import API_KEY_ASSEMBLYAI, API_KEY_LISTENNOTES

transcript_endpoint = 'https://api.assemblyai.com/v2/transcript'
headers_assemblyai = {
    "authorization": API_KEY_ASSEMBLYAI,
    "content-type": "application/json"
}
listennotes_episode_endpoint = 'https://listen-api.listennotes.com/api/v2/episodes'
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
        try:
            filename_text = f"{episode_id}.txt"
            with open(filename_text, 'w') as f:
                f.write(data['text'])
                print('Text transcript saved to:', filename_text)
            
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
                print('JSON transcript saved to:', filename_json)
            
            return True
        except Exception as e:
            print("Error occurred while saving transcript:", str(e))
            return False
    
    elif error:
        print("Error:", error)
        return False

if __name__ == "__main__":
    episode_id = "your_episode_id_here"
    save_transcript(episode_id)
import requests
import json
import time
from api_secrets import API_KEY_ASSEMBLYAI, API_KEY_LISTENNOTES
import pprint


transcript_endpoint = 'https://api.assemblyai.com/v2/transcript'
assemblyai_headers = {"authorization": API_KEY_ASSEMBLYAI}


listennotes_episode_endpoint = 'https://listen-api.listennotes.com/api/v2/episodes'
headers_listennotes = {'X-ListenAPI-Key': API_KEY_LISTENNOTES,}


def get_episode_audio_url(episode_id):
    url = listennotes_episode_endpoint + '/' + episode_id
    response = requests.request('GET', url, headers=headers_listennotes)

    data = response.json()
    # pprint.pprint(data)

    episode_title = data['title']
    thumbnail = data['thumbnail']
    podcast_title = data['podcast']['title']
    audio_url = data['audio']
    return audio_url, thumbnail, podcast_title, episode_title

def transcribe(audio_url, auto_chapters):
    transcript_request = {
        'audio_url': audio_url,
        'auto_chapters': auto_chapters
    }

    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=assemblyai_headers)
    pprint.pprint(transcript_response.json())
    return transcript_response.json()['id']


def poll(transcript_id):
    polling_endpoint = transcript_endpoint + '/' + transcript_id
    polling_response = requests.get(polling_endpoint, headers=assemblyai_headers)
    return polling_response.json()
    


def get_transcription_result_url(url, auto_chapters):
    transcribe_id = transcribe(url, auto_chapters)
    while True:
        data = poll(transcribe_id)
        if data['status'] == 'completed':
            return data, None
        elif data['status'] == 'error':
            return data, data['error']

        print("waiting for 60 seconds")
        time.sleep(60)
            

def save_transcript(episode_id):
    audio_url, thumbnail, podcast_title, episode_title = get_episode_audio_url(episode_id)
    data, error = get_transcription_result_url(audio_url, auto_chapters=True)
    if data:
        filename = episode_id + '.txt'
        with open(filename, 'w') as f:
            f.write(data['text'])

        filename = episode_id + '_chapters.json'
        with open(filename, 'w') as f:
            chapters = data['chapters']

            data = {'chapters': chapters}
            data['audio_url']=audio_url
            data['thumbnail']=thumbnail
            data['podcast_title']=podcast_title
            data['episode_title']=episode_title
            # for key, value in kwargs.items():
            #     data[key] = value

            json.dump(data, f, indent=4)
            print('Transcript saved')
            return True
    elif error:
        print("Error!!!", error)
        return False

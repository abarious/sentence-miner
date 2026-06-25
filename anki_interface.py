import requests
import json

ANKI_URL = "http://127.0.0.1:8765"

def invoke(action, **params):
    return requests.post(ANKI_URL, json={
        "action": action,
        "version": 6,
        "params": params
    }).json()

def addNote(deck_name, model_name, fields):
    note = {
        "deckName": deck_name,
        "modelName": model_name,
        "fields": fields,
        "tags": ["auto"] 
    }
    return invoke("addNote", note=note)

def addMediaFile(file_name, file_data):
    return invoke("storeMediaFile", filename=file_name, data=file_data)
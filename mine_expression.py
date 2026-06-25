from urllib import response

from google import genai
import pyperclip
import json
import os
import sys
import base64

from gtts import gTTS
from io import BytesIO
import anki_interface as anki

SYSTEM_PROMPT = """
## Task: English Vocabulary Explanation 

You are helping me learn English vocabulary.

## Input Format

I will provide one or more English sentences. Some words or phrases are marked in Markdown bold (**item**).
Each sentence may contain multiple bolded items, and ALL must be processed.
This is very important so I repeat: ALL bolded items must be processed even if there are multiple in a sentence.

The bolded items may be:
* a single word
* a multi-word phrase
* an idiom or expression

Only explain the bolded items.

Example input:
- He gave me a **cold shoulder** after the meeting
- She **turned down** the offer because it was **too good to be true** (multiple bolded items in one sentence case)

---

## Task

For each sentence:

1. Find ALL bolded items (**...**) in the sentence.
2. Treat each bolded item as a SINGLE unit (do not split phrases into words).
3. You MUST explain EVERY bolded item in the sentence.
4. Do NOT stop after the first item.
5. The number of explanations MUST exactly match the number of bolded items.

For each bolded item:

* Provide a concise, simple definition (B1-B2 level) based on context.
* Use simple English only.
* If multiple meanings exist, use ONLY the meaning that fits the sentence context.
* Provide IPA pronunciation (General American English).
* Provide 1-2 synonyms (only if appropriate to the context).
* Provide 2 example sentences using the same meaning.

---

## Critical Rule (Very Important)

Before generating output:
- Count how many bolded items exist in each sentence.
- Your output MUST contain exactly the same number of items in the "items" array.
- Process items from left to right in the sentence.

---

## Output Format

Return ONLY valid JSON. No markdown, no comments, no extra text.

Schema:

{
  "results": [
    {
      "sentence": "<original sentence>",
      "items": [
        {
          "item": "<word or phrase>",
          "pronunciation": "<IPA pronunciation>",
          "definition": "<simple context-specific definition>",
          "synonyms": [
            "<synonym1>",
            "<synonym2>"
          ],
          "examples": [
            "<example1>",
            "<example2>"
          ]
        }
      ]
    }
  ]
}

---

## Output Example

Input:
- He gave me a **cold shoulder** after the meeting.

Output:
{
  "results": [
    {
      "sentence": "He gave me a cold shoulder after the meeting.",
      "items": [
        {
          "item": "cold shoulder",
          "pronunciation": "/ˌkoʊld ˈʃoʊldər/",
          "definition": "To ignore someone or act unfriendly toward them.",
          "synonyms": [
            "ignore",
            "reject"
          ],
          "examples": [
            "She gave him the cold shoulder after the argument.",
            "He felt bad when they gave him the cold shoulder."
          ]
        }
      ]
    }
  ]
}

---

## Multiple Items Example (Very Very Very Important)

Input:
- She **turned down** the offer because it was **too good to be true**.

Output:
{
  "results": [
    {
      "sentence": "She turned down the offer because it was too good to be true.",
      "items": [
        {
          "item": "turned down",
          "pronunciation": "/ˌtɝːnd ˈdaʊn/",
          "definition": "Rejected or refused something.",
          "synonyms": [
            "reject",
            "refuse"
          ],
          "examples": [
            "He turned down the job offer.",
            "She turned down their invitation."
          ]
        },
        {
          "item": "too good to be true",
          "pronunciation": "/tuː ɡʊd tə bi truː/",
          "definition": "So good that it seems not real or not honest.",
          "synonyms": [
            "unbelievable",
            "suspicious"
          ],
          "examples": [
            "The deal looked too good to be true.",
            "The offer was too good to be true."
          ]
        }
      ]
    }
  ]
}

---

## Important

- Every field in the JSON must contain plain text only.
- No Markdown (**), no backticks, no formatting symbols.
- Example: 
  Input: He gave me a **cold shoulder** after the meeting. 
  Output sentence in JSON: He gave me a cold shoulder after the
- The output must be valid JSON only.
- Each sentence may contain multiple bolded items, and ALL must be processed.
"""

def getAPIKey():
    key_file_path = "key.txt"
    if not os.path.exists(key_file_path):
        raise FileNotFoundError(f"API key file '{key_file_path}' not found.")
    
    with open(key_file_path, "r") as f:
        api_key = f.read().strip()
    
    if not api_key:
        raise ValueError("API key is empty. Please provide a valid API key in 'key.txt'.")
    
    return api_key

def lookupExpressions(sentences, prompt=None):

    llm_api_key = getAPIKey() 
    client = genai.Client(api_key=llm_api_key)

    sentences_input = "\n".join("- " + sentence for sentence in sentences)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=SYSTEM_PROMPT + "\n\n " + sentences_input
    )

    json_str = response.text.strip()
    if json_str.startswith("```") and json_str.endswith("```"):
        json_str = json_str.split("\n", 1)[1]
        json_str = json_str.rsplit("```", 1)[0]
    data = json.loads(json_str)['results']
    return data


def getExpressionAudio(expr):
    buffer = BytesIO()
    gTTS(expr, lang='en').write_to_fp(buffer)
    audio_data = base64.b64encode(buffer.getvalue()).decode()
    return audio_data


def addExpressionsDataToAnki(data):

    deck_name = "English-Learning::Mined-Expressions"
    model_name = "Refold Sentence Miner: Sentence"

    for expr_data in data:
        expr_fields = {}
        sentence = expr_data.get("sentence", "")
        expr_fields["sentence"] = sentence
        items = expr_data.get("items", [])
        for item in items:
            expr_fields["expression"] = item.get("item", "")
            expr_fields["pronunciation"] = item.get("pronunciation", "")
            expr_fields["definition"] = item.get("definition", "")
            expr_fields["synonym1"] = item["synonyms"][0] if len(item["synonyms"]) > 0 else ""
            expr_fields["synonym2"] = item["synonyms"][1] if len(item["synonyms"]) > 1 else ""
            expr_fields["example1"] = item["examples"][0] if len(item["examples"]) > 0 else ""
            expr_fields["example2"] = item["examples"][1] if len(item["examples"]) > 1 else ""

            audio_data = getExpressionAudio(expr_fields["expression"])
            audio_filename = f"{expr_fields["expression"].replace(' ', '-')}.mp3"
            anki.addMediaFile(audio_filename, audio_data)
            expr_fields["expression_audio"] = f"[sound:{audio_filename}]"

            anki.addNote(deck_name, model_name, expr_fields)

#################################################################
try:
    sentences = pyperclip.paste().split("\n")
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    sentences = [sentence.replace("- [ ] ", "") for sentence in sentences]
    data = lookupExpressions(sentences, prompt=SYSTEM_PROMPT)
    addExpressionsDataToAnki(data)
    sys.exit(0)

except Exception as e:
    print(e)
    sys.exit(1)


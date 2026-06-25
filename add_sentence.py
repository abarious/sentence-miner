import pyperclip
import sys

PATH = "D:\\english-learning\\mined_sentences.md"

try:
    sentence = pyperclip.paste()
    with open(PATH, "a", encoding="utf-8") as file:
        file.write("- [ ] " + sentence + "\n")

    sys.exit(0)
except Exception as e:
    print(e)
    sys.exit(1)
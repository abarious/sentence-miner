^!+x:: {
    Send "^c"
    Sleep 200

    RunWait 'python "D:\sentence-miner\add_sentence.py"'

    if (A_LastError = 0)
        MsgBox "Sentence added successfully!"
    else
        MsgBox "Failed to add sentence."
}

^!+z:: {
    Send "^c"
    Sleep 200

    RunWait 'python "D:\sentence-miner\mine_expression.py"'

    if (A_LastError = 0)
        MsgBox "Expressions added to Anki successfully!"
    else
        MsgBox "Failed to add expressions to Anki."
}
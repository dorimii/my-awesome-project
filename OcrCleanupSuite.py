# Here we apply our methods to correct the most common OCR errors to make the texts more legible for humans and AIs.
# We thought there was a more standard solution for this but, no, turns out custom Regexes are the best/only way to
# tackle this problem. Executing this for 2.4GB of text also only took 5 minutes.

import os
import re

source_directory = 'ANNO Raw/Zeitschriften'
destination_directory = 'ANNO Cleaned/Zeitschriften'


def clean_text(text):
    # This is to weed out garbled short lines, artefact clusters.
    # Lines containing fewer than 4 lexical chars and blocks of 3 lines shorter than
    # 15 chars are removed
    lines = text.split('\n')
    cleaned_lines = []
    block_count = 0

    lexical_chars = re.compile(r'[a-zA-Z]')

    for i in range(len(lines)):
        if len(lexical_chars.findall(lines[i])) >= 4:
            cleaned_lines.append(lines[i])
            block_count = 0

        elif len(lines[i]) < 15:
            # If the line is shorter than 15 characters, check for a block of three such lines
            if i+2 < len(lines) and all(len(lines[j]) < 15 for j in range(i, i+3)):
                block_count = 3
            elif block_count > 0:
                block_count -= 1
            else:
                cleaned_lines.append(lines[i])
        else:
            cleaned_lines.append(lines[i])

    return '\n'.join(cleaned_lines)


def main():

    # Regex containing all chars that we allow. This gets rid of many illegible symbols.
    legal_characters = re.compile('[^a-zA-ZäöüßÄÖÜ.,!?+%&=()0123456789:; \-\n]')
    # Regex to sniff out repeating punctuation, a common OCR error
    repeating_punctuation = re.compile(r'([.,!?"+%&=():;-])([.,!?"+%&=(:;-])')
    # Regex to undo the commonly e m p h a s i s e d spelling of Eigenwörter
    spaced_word_pattern = re.compile(r'(\b(?:[a-zA-Z]\s)+[a-zA-Z]\b)')
    # Regex to fix the letter 'S' being very often capitalized when it appears at the end of wordS
    capital_S_pattern = re.compile(r'([a-zA-Z])(S)')

    for folder in os.listdir(source_directory):
        folder_path = os.path.join(source_directory, folder)
        subfolder_path = os.path.join(folder_path, '1900')

        if os.path.isdir(subfolder_path):
            files = os.listdir(subfolder_path)

            if files:

                for filename in files:

                    source_file_path = os.path.join(source_directory, folder, '1900', filename)
                    destination_file_path = os.path.join(destination_directory, folder, '1900', filename)

                    with open(source_file_path, 'r', encoding='utf-8') as file:
                        content = file.read()

                    hosed_text = legal_characters.sub('', content)

                    # r'\1' leaves only the left punctuation character
                    washed_text = repeating_punctuation.sub(r'\1', hosed_text)
                    # This leaves the left character and replaces the second with a lowercase s
                    wet_text = capital_S_pattern.sub(r'\1s', washed_text)

                    cleaned_text = clean_text(wet_text)

                    deemphasised_cleaned_text = re.sub(spaced_word_pattern, lambda match: ''.join(match.group().split()), cleaned_text)

                    with open(destination_file_path, 'w', encoding='utf-8') as file:
                        file.write(deemphasised_cleaned_text)


if __name__ == "__main__":
    main()

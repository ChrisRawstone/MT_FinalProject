
import pandas as pd
import numpy as np


numberOfSentences=10000

# Read in danish and english sentence pairs (first 10 sentences)
danishlines = open("europarl-v7da.txt",encoding="utf8").read().splitlines()[0:numberOfSentences]
englishlines = open("europarl-v7en.txt",encoding="utf8").read().splitlines()[0:numberOfSentences]

# Create pandas data structure with three columns: idx, danish sentences, english sentences
d = {"Danish" : danishlines, "English" : englishlines}
df = pd.DataFrame(d)


# Calculate sentence complexity for a given sentence
def findcomplexity(s):
    sentence = s.strip()
    countWords = 1
    countChars = 0
    for i, letter in enumerate(sentence):
        if letter == " ":
            countWords += 1
        else:
            countChars += 1

    complexity = 4.71 * (countChars / countWords) + 0.5 * (countWords / 1) - 21.43
    return complexity


# apply complexity to each danish and english sentence and calculate average between them m
df["Da_ARI"] = df.apply(lambda row : findcomplexity(row['Danish']), axis = 1)
df["En_ARI"] = df.apply(lambda row : findcomplexity(row['English']), axis = 1)
df["Avg_ARI"] = df.apply(lambda row: (row["En_ARI"] + row["Da_ARI"]) / 2, axis = 1)

# sort by average sentence complexity
df = df.sort_values(by ='Avg_ARI')

# create numpy array for both Danish and English sentence columns
# necessary to get them in proper form of DanishSentence|||EnglishSentence

mask = ((df['Danish'].str.len() < 20) & (df['Danish'].str.len() > 2) & (df['English'].str.len() > 2))
df = df.loc[mask]

npDan=df["Danish"].to_numpy()
npEng=df["English"].to_numpy()

# npDan = df[df.Danish.str.len() < 10].to_numpy()

# npDan=df["Danish"].to_numpy()
# npEng=df["English"].to_numpy()

# Populating the file with correct line separation
f = open("data/traindata.txt", "w", encoding='utf-8')
for sentenceNumber in range(npDan.size):
    print(npDan[sentenceNumber],"|||", npEng[sentenceNumber])
    # print(npEng[sentenceNumber])
    f.write(f"{npDan[sentenceNumber]}|||{npEng[sentenceNumber]}\n")

f.close()

# df.to_csv("danish_english.csv",encoding='utf-8')




import pandas as pd
import numpy as np
import random

random.seed(0)

#Total amount of sentences: 1968800



# Read in danish and english sentence pairs (first 10 sentences)


danishlines = open("europarl-v7da.txt",encoding="utf8").read().splitlines()[0:30000]
englishlines = open("europarl-v7en.txt",encoding="utf8").read().splitlines()[0:30000]



danishlinestrain = danishlines[0:20000]
englishlinestrain = englishlines[0:20000]
danishlinesval = danishlines[20000:22000]
englishlinesval = englishlines[20000:22000]
danishlinestest = danishlines[22000:24000]
englishlinestest = englishlines[22000:24000]



# Create pandas data structure with three columns: idx, danish sentences, english sentences
dtrain = {"Danish" : danishlinestrain, "English" : englishlinestrain}
dtest = {"Danish" : danishlinestest, "English" : englishlinestest}
dval = {"Danish" : danishlinesval, "English" : englishlinesval}
dftrain = pd.DataFrame(dtrain)
dftest = pd.DataFrame(dtest)
dfval = pd.DataFrame(dval)

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
def apply_functions_and_filterings(df,filename):


    df["Da_ARI"] = df.apply(lambda row : findcomplexity(row['Danish']), axis = 1)
    df["En_ARI"] = df.apply(lambda row : findcomplexity(row['English']), axis = 1)
    df["Avg_ARI"] = df.apply(lambda row: (row["En_ARI"] + row["Da_ARI"]) / 2, axis = 1)

    # shuffled = df.sample(frac=1, random_state=1).reset_index()

    # sort by average sentence complexity
    # df = df.sort_values(by ='Avg_ARI')

    # create numpy array for both Danish and English sentence columns
    # necessary to get them in proper form of DanishSentence|||EnglishSentence

    #Limit sentences:
    CharacterLength = 50

    mask = ((df['Danish'].str.len() < CharacterLength) & (df['Danish'].str.len() > 2) & (df['English'].str.len() > 2) & (df['English'].str.len() < CharacterLength))
    df = df.loc[mask]

    df['Danish'] = df['Danish'].str.replace("([^ÆØÅæøåa-zA-Z0-9\\s.,?!])", "")
    df['English'] = df['English'].str.replace("([^ÆØÅæøåa-zA-Z0-9\\s.,?!])", "")


    npDan = df["Danish"].to_numpy()
    npEng = df["English"].to_numpy()

    # Populating the file with correct line separation
    f = open(f"data/{filename}.txt", "w", encoding='utf-8')
    for sentenceNumber in range(npDan.size):
        # print(npDan[sentenceNumber], "|||", npEng[sentenceNumber])
        # print(npEng[sentenceNumber])
        f.write(f"{npDan[sentenceNumber]}|||{npEng[sentenceNumber]}\n")

    # for sentenceNumber in range(shuffled.size):
    #     print(shuffled["Da_ARI"], "|||", shuffled["En_ARI"])

    f.close()




dftrain=apply_functions_and_filterings(dftrain,"traindataToo")
dftest=apply_functions_and_filterings(dftest,"testdataToo")
dfval=apply_functions_and_filterings(dfval,"validationdataToo")


# npDan = df[df.Danish.str.len() < 10].to_numpy()



# df.to_csv("danish_english.csv",encoding='utf-8')



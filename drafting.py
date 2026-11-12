import numpy as np
import pandas as pd
import itertools

dir = "data/models/gravity/"

# Small snippet to reformat the original gggrx1200 file. 
def reformatGGGRX(filename= "gggrx_1200l_sha.tab",
                  reformatedName= "gggrx_1200l_formatted.csv"):
    df = pd.read_csv(dir + filename)

    df = df.drop(columns=df.columns[[4, 5]])
    df = df.dropna(axis=1, how="all")

    df.to_csv(dir + reformatedName, index=False)

    return None


# Reformat the original LP150Q file. 
if reformatLPQ150 := False:
    df = pd.read_csv(dir + "jgl150q1.sha")

    df = df.drop(columns=df.columns[[4, 5]])
    df = df.dropna(axis=1, how="all")

    df.to_csv(dir + "lp150q_formatted.csv", index=False)

testDict = dict()
testDict["A"] = [1,2,3]
testDict["B"] = [1,3,5]

emptyArr = np.empty((3*3,2))

i = 0
for combination in itertools.product( *testDict.values() ):
    emptyArr[i,:] = combination
    currentSettings = dict( zip( testDict.keys(), combination ) )
    i+=1

print( emptyArr )
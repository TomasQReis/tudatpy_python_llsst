import numpy as np
import pandas as pd

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

arr1 = np.array([1,2])
arr2 = np.array([1,2,3,4])

combinations = np.empty( ( (len(arr1)*len(arr2)) , 2) ) 

print( np.shape( combinations ) )

for i in range(len(arr1)):
    for j in range(len(arr2)):
        rowIdx = i*len(arr2) + j
        combinations[rowIdx] = [arr1[i], arr2[j]]

print( combinations )
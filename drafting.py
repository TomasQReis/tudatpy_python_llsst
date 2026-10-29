import numpy as np
import pandas as pd

dir = "data/models/gravity/"

# Small snippet to reformat the original gggrx1200 file. 
if reformatGGGRX := False:
    df = pd.read_csv(dir + "gggrx_1200l_sha.tab")

    df = df.drop(columns=df.columns[[4, 5]])
    df = df.dropna(axis=1, how="all")

    df.to_csv(dir + "gggrx_1200l_formatted.csv", index=False)

# Reformat the original LP150Q file. 
if reformatLPQ150 := False:
    df = pd.read_csv(dir + "jgl150q1.sha")

    df = df.drop(columns=df.columns[[4, 5]])
    df = df.dropna(axis=1, how="all")

    df.to_csv(dir + "lp150q_formatted.csv", index=False)

harmonicsDegree = np.array([1,2,3,4])
sumOfCosCoeffsSqrd = np.sum( harmonicsDegree**2 )
print(harmonicsDegree**2)
print(sumOfCosCoeffsSqrd)
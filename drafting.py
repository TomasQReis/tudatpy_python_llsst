import numpy as np
import pandas as pd

# Small snippet to reformat the original gggrx1200 file. 
if reformatGGGRX := True:
    dir = "data/models/gravity/"

    df = pd.read_csv(dir + "gggrx_1200l_sha.tab")

    df = df.drop(columns=df.columns[[4, 5]])
    df = df.dropna(axis=1, how="all")

    df.to_csv(dir + "gggrx_1200l_formatted.csv", index=False)
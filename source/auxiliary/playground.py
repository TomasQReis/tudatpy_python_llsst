import numpy as np

size = 4

testArr = np.zeros([size,size])

testArr = np.arange(1, stop= 17, step= 1)

maxDegree = 5

degreeRange = np.arange(2, maxDegree +1)
degrees = np.repeat(degreeRange, degreeRange + 1)
orders = np.concatenate([np.arange(d + 1) for d in degreeRange])

print(degrees)
print(orders)

index = np.where( orders == 0 )[0]

testArr = np.ones(np.size(degrees) - 4)

finalArr = np.zeros(np.size(degrees))

mask = np.ones(np.size(degrees), dtype= bool)
mask[index] = False

finalArr[mask] = testArr

print(testArr)
print(orders)
print(finalArr)

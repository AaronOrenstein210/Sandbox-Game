import numpy as np

arr = np.full((10, 10), 0, dtype=np.int)
col = [1] * 10
print(arr)
arr[:, 5] = col
print(arr)
arr[5, :] = col
print(arr)

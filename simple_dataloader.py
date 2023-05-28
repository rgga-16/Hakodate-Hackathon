# Script to generate pickle files
import json
import pickle

data_path = input('>>')

store = {}

with open(data_path,encoding='utf-8') as f:
    origin_data = json.load(f)

    data_tmp = []
    for category in origin_data:
        for line in origin_data[category]:
            data_tmp.append(line)
        store[category] = data_tmp

print(store)

with open('datastore.pickle','wb') as f:
    pickle.dump(store,f)
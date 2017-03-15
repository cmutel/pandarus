import requests
import os
import hashlib
import time
import pprint


"""Test Pandarus remote.

Need to have:

* Flask app running. Do something like (from the pandarus_remote main directory):
    export FLASK_APP=pandarus_remote/__init__.py
    export FLASK_DEBUG=1
    flask run

* Rq worker (anywhere, but in correct virtualenv):
    rq worker

* Redis
    redis-server

"""

def sha256(filepath, blocksize=65536):
    """Generate SHA 256 hash for file at `filepath`"""
    hasher = hashlib.sha256()
    fo = open(filepath, 'rb')
    buf = fo.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = fo.read(blocksize)
    return hasher.hexdigest()

url = 'http://127.0.0.1:5000'
# url = 'https://pandarus.brightwaylca.org'

print("Ping!")
print(requests.get(url).text)

print("Checking basic data upload")

os.chdir("data")

fp = 'grid.geojson'
print(fp)
data = {
    'field': 'name',
    'name': os.path.basename(fp),
    'sha256': sha256(fp),
    'layer': '',
    'band': ''
}
resp = requests.post(url + '/upload', data=data, files={'file': open(fp, 'rb')})
assert resp.status_code == 200

fp = 'square.geojson'
print(fp)
data = {
    'field': 'name',
    'name': os.path.basename(fp),
    'sha256': sha256(fp),
    'layer': '',
    'band': ''
}
resp = requests.post(url + '/upload', data=data, files={'file': open(fp, 'rb')})
assert resp.status_code == 200

fp = 'range.tif'
print(fp)

data = {
    'field': '',
    'name': os.path.basename(fp),
    'sha256': sha256(fp),
    'layer': '',
    'band': '1'
}

resp = requests.post(url + '/upload', data=data, files={'file': open(fp, 'rb')})
assert resp.status_code == 200

print('Catalog:')
pprint.pprint(requests.get(url + '/catalog').json())

print("Check intersections")
data = {
    'first': sha256('square.geojson'),
    'second': sha256('grid.geojson')
}
resp = requests.post(url + "/calculate-intersection", data=data)
assert resp.status_code == 200

time.sleep(3)

print("Check remaining")
resp = requests.post(url + "/calculate-remaining", data=data)
assert resp.status_code == 200

print("Check raster stats")
data = {
    'raster': sha256('range.tif'),
    'vector': sha256('grid.geojson')
}

resp = requests.post(url + "/calculate-rasterstats", data=data)
assert resp.status_code == 200

time.sleep(3)

print('Catalog:')
pprint.pprint(requests.get(url + '/catalog').json())

print("Retrieving data")

print("Raster stats")
data = {
    'raster': sha256('range.tif'),
    'vector': sha256('grid.geojson')
}
resp = requests.post(url + "/rasterstats", data=data)
assert resp.status_code == 200

print("Intersection")
data = {
    'first': sha256('square.geojson'),
    'second': sha256('grid.geojson')
}
resp = requests.post(url + "/intersection", data=data)
assert resp.status_code == 200

resp = requests.post(url + "/intersection-file", data=data)
assert resp.status_code == 200

print("Remaining")
resp = requests.post(url + "/remaining", data=data)
assert resp.status_code == 200

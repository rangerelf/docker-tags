# docker-tags
Retrieve the versions of the given docker image
to stdout. Optionally, log the raw json received
from the hub to a file.

### Usage:
From the command line:
```
usage: docker_tags.py [-h] [--json JSON] images [images ...]

docker_tags.py

positional arguments:
  images       Docker images to check

optional arguments:
  -h, --help   show this help message and exit
  --json JSON  Stream received json to this file
```

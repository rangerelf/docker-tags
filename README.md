# docker-tags
Retrieve the versions of the given docker image
to stdout. Optionally, log the raw json received
from the hub to a file.

### Usage:
From the command line:
```
$ ./docker_tags.py -h
usage: docker_tags.py [-h] [--all] [--report REPORT] images [images ...]

Query the public docker hub for available versions of one or more
repositories.

positional arguments:
  images           Docker images to check

optional arguments:
  -h, --help       show this help message and exit
  --all            Don't omit any architectures (386, arm/v6, arm/v7, ppc64le,
                   s390x)
  --report REPORT  Set the report type to use (brief|detailed|js|raw)

```

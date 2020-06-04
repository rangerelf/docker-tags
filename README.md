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
  --all            Don't omit any architectures (386, arm/v5, arm/v6, arm/v7,
                   ppc64le, s390x)
  --report REPORT  Set the report type to use (brief|detailed|js|raw)
```

### Example brief output
Here's some example outputs:

```sh
$ ./docker_tags.py postgres
Omitting these architectures: s390x, ppc64le, arm/v6, arm/v7, 386, arm/v5
postgres:13-beta1 ? [amd64:L, arm64/v8:L, mips64le:L]
postgres:13 ? [amd64:L, arm64/v8:L, mips64le:L]
postgres:13-beta1-alpine ? [amd64:L, arm64/v8:L]
postgres:13-alpine ? [amd64:L, arm64/v8:L]
postgres:alpine ? [amd64:L, arm64/v8:L]
postgres:9.6.18-alpine ? [amd64:L, arm64/v8:L]
postgres:9.6-alpine ? [amd64:L, arm64/v8:L]
postgres:9-alpine ? [amd64:L, arm64/v8:L]
postgres:12.3-alpine ? [amd64:L, arm64/v8:L]
postgres:12-alpine ? [amd64:L, arm64/v8:L]
postgres:latest ? [amd64:L, arm64/v8:L, mips64le:L]
postgres:11.8-alpine ? [amd64:L, arm64/v8:L]
postgres:11-alpine ? [amd64:L, arm64/v8:L]
postgres:10.13-alpine ? [amd64:L, arm64/v8:L]
postgres:10-alpine ? [amd64:L, arm64/v8:L]
postgres:9.6.18 ? [amd64:L, arm64/v8:L, mips64le:L]
postgres:9.6 ? [amd64:L, arm64/v8:L, mips64le:L]
postgres:9.5.22-alpine ? [amd64:L, arm64/v8:L]
postgres:9.5.22 ? [amd64:L, arm64/v8:L, mips64le:L]
postgres:9.5-alpine ? [amd64:L, arm64/v8:L]
....

$ ./docker_tags.py vbatts/slackware
Omitting these architectures: 386, s390x, arm/v7, arm/v6, arm/v5, ppc64le
vbatts/slackware:latest 33.23MB [amd64:L]
vbatts/slackware:current 52.16MB [amd64:L]
vbatts/slackware:14.2 33.23MB [amd64:L]
vbatts/slackware:13.37 27.89MB [amd64:L]
vbatts/slackware:14.0 29.43MB [amd64:L]
vbatts/slackware:14.1 30.66MB [amd64:L]

$
```

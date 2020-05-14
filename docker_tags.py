#!/data/data/com.termux/files/usr/bin/python
"""
docker_tags.py
"""
import sys
import json
import urllib.request

HUB_URL = "https://registry.hub.docker.com/v2/repositories/{}{}/tags/"

KB = 1024.0
MB = 1024*1024.0
GB = 1024*1024*1024.0

class BadResponseStatus(ValueError):
    "Request returned a bad response status."

def get(url, log_json=False):
    "Returns the json blob from the given url"
    rsp = urllib.request.urlopen(url)
    if 200 <= rsp.getcode() < 300:
        text = rsp.read()
        if log_json:
            log_json.write(text.decode('utf8'))
        return json.loads(text)
    raise BadResponseStatus(rsp.getcode())

def hrn(num):
    "Human-readable-number"
    if num:
        if num < KB:
            return '{:,}B'.format(num)
        if num < MB:
            return '%.01fKB' % (num / KB)
        if num < GB:
            return '%.02fMB' % (num / MB)
        return '%.02fGB' % (num / GB)
    return '???'

def run_report(tags, json_log=None):
    "Report all versions for a given tag"
    try:
        for name in tags:
            fmt = "%s:%%(name)s (%%(mb)s)" % name
            url = HUB_URL.format('' if '/' in name else 'library/', name)
            while url:
                page = get(url, log_json=json_log)
                for tag in page["results"]:
                    print(fmt % {"mb": hrn(tag["full_size"]), **tag})
                url = page.get("next")
    except KeyboardInterrupt:
        print("")

def main():
    "Run from the command line"
    from argparse import ArgumentParser, FileType
    agp = ArgumentParser(description=__doc__)
    agp.add_argument("--json", action="store", default=None,
            type=FileType('w'),
            help="Stream received json to this file")
    agp.add_argument("images", nargs="+",
            help="Docker images to check")
    args = agp.parse_args()
    run_report(args.images, json_log=args.json)

if __name__ == "__main__":
    main()
# Done.

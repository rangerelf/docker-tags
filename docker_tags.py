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

def backfill_results(page_data, params={}):
    "Add some items we need for the report"
    for item in page_data['results']:
        item.update(params)
        item['readable_size'] = hrn(tag['full_size'])
    return page_data

def get(name_or_url, log_json=False, backfill_params={}):
    "Returns the json blob from the given url"
    if name_or_url.startswith('http:') \
    or name_or_url.startswith('https:'):
        url = name_or_url
    elif '/' in 
        url = HUB_URL.format('', name)
    else:
        url = HUB_URL.format('library/', name)
    rsp = urllib.request.urlopen(url)
    if 200 <= rsp.getcode() < 300:
        text = rsp.read()
        if log_json:
            log_json.write(text.decode('utf8'))
        return backfill_results(json.loads(text), backfill_params)
    raise BadResponseStatus(rsp.getcode())

def run_report(tags, **kwarg):
    "Report all versions for a given tag"
    jsl = kwarg.get('json_log')
    template = kwarg.get('template')
    try:
        for name in tags:
            bfp = {'repository_name': name}
            next_page = name
            while next_page:
                page = get(next_page, log_json=jsl, backfill_params=bfp)
                next_page = page.get('next')
                if template:
                    for tag in page["results"]:
                        print(template.format(**tag))
                else:
                    comma = "," if next_page else ""
                    print(json.dumps(page, indent=2)+comma)
    except KeyboardInterrupt:
        print("")

TEMPLATES = {
    'short': '{repository_name}: {name} ({readable_size})'
}

def main():
    "Run from the command line"
    from argparse import ArgumentParser, FileType
    agp = ArgumentParser(description=__doc__)
    agp.add_argument("--json", action="store", default=None,
            type=FileType('w'),
            help="Stream received json to this file")
    agp.add_argument("images", nargs="+",
            help="Docker images to check")
    tgrp = agp.add_mutually_exclusive_group()
    tgrp.add_argument("--template", "-t", action="store", default="short",
            help="Set the report template")
    tgrp.add_argument("--raw", action="store_true", default=False,
            help="Output raw json instead of a report")
    args = agp.parse_args()
    if args.raw:
        fmt = None
    elif args.template.startswith('format:'):
        fmt = args.template.lstrip('format:')
    elif args.template in TEMPLATES:
        fmt = TEMPLATES[args.template]
    else:
        agp.error("Unknown formatting argument")
    run_report(args.images, json_log=args.json, template=fmt)

if __name__ == "__main__":
    main()
# Done.

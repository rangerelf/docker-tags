#!/usr/bin/env python3
# pylint: disable=bad-continuation
"""
docker_tags.py
"""
import json
import urllib.request

DOCKER_HUB_REGISTRY = "https://registry.hub.docker.com"

def hrn(num, magnitude=1024):
    "Human-readable-number"
    if num < magnitude:
        return f"{num:,}B"
    ## Up to PetaBytes should be more than enough.
    for mag in 'KMGTP':
        num, frac = divmod(num, magnitude)
        if num < magnitude:
            return f"{num:,}.{(100*frac//1024):02}{mag}B"
    return f"{num:,}.{(100*frac//1024):02}PB"

def backfilled(page_data, params):
    "Add some items we need for the report"
    for item in page_data['results']:
        item.update(params)
        item['readable_size'] = hrn(item['full_size'])
    return page_data

class BadResponseStatus(ValueError):
    "Request returned a bad response status."

def get(url, log_json=None, backfill_params=None):
    "Iterate the data pages from the given url"
    while url:
        rsp = urllib.request.urlopen(url)
        if not 200 <= rsp.getcode() < 300:
            raise BadResponseStatus(rsp.getcode())
        text = rsp.read()
        if log_json:
            log_json.write(text.decode('utf8'))
        data = json.loads(text)
        yield backfilled(data, backfill_params or {})
        url = data.get('next')

def repo_url(name, registry=DOCKER_HUB_REGISTRY):
    "Yield each url created from the repo names in 'names'"
    prefix = f"{registry}/v2/repositories"
    if '/' in name:
        return f"{prefix}/{name}/tags/"
    return f"{prefix}/library/{name}/tags/"

def run_report(docker_repos, **kwarg):
    "Report versions of images found in 'docker_repositories'"
    jsl = kwarg.get('json_log')
    template = kwarg.get('template')
    try:
        for name in docker_repos:
            bfp = {'repository_name': name}
            for page in get(repo_url(name), log_json=jsl, backfill_params=bfp):
                if template:
                    for tag in page["results"]:
                        print(template.format(**tag))
                else:
                    comma = "," if page.get('next') else ""
                    print(json.dumps(page, indent=2)+comma)
    except KeyboardInterrupt:
        print("")

# Dictionary of callables with the format.
TEMPLATES = {
    'short': "{repository_name}: {name} ({readable_size})"
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

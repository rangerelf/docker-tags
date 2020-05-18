#!/usr/bin/env python3
# pylint: disable=bad-continuation,eval-used
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

class BadResponseStatus(ValueError):
    "Request returned a bad response status."

def get(url, json_log=None):
    "Iterate the data pages from the given url"
    while url:
        rsp = urllib.request.urlopen(url)
        if not 200 <= rsp.getcode() < 300:
            raise BadResponseStatus(rsp.getcode())
        text = rsp.read()
        if json_log:
            json_log.write(text.decode('utf8'))
        data = json.loads(text)
        yield data
        url = data['next']

def repo_url(name, registry=DOCKER_HUB_REGISTRY):
    "Yield each url created from the repo names in 'names'"
    if '/' in name:
        return f"{registry}/v2/repositories/{name}/tags/"
    return f"{registry}/v2/repositories/library/{name}/tags/"

def brief_report(docker_repos, **kwarg):
    "One line per docker tag version"
    jsl = kwarg.get('json_log')
    for nth, repo_name in enumerate(docker_repos):
        if nth:
            print("="*64)
        for page in get(repo_url(repo_name), json_log=jsl):
            version = page["name"]
            size = hrn(page["full_size"])
            arch = ", ".join(_["arch"] for _ in page["images"])
            print(f"{repo_name}:{version} Size: {size} Arch: {arch}")

def report(report_obj, docker_repo, json_log):
    "Send out the report"
    for nth, repo_name in enumerate(docker_repos):
        if nth:
            report_obj.separator()
        for page in get(repo_url(repo_name), json_log=jsl):
            report_obj.page(repo_name, page)

class Report:
    def __init__(self, stream):
        self._stream = stream 
    def report(self, docker_repos, json_log):
        "The main report loop"
        repo_num = 0 # Have to pre-initialize repo_num ...
        for repo_num, repo_name in enumerate(docker_repos):
            if repo_num:
                self.separator()
            url = repo_url(repo_name)
            for page_num, page in enumerate(url, json_log=json_log):
                self.report_page(repo_num, repo_name, page_num, page)
        # because if docker_repos is empty then repo_num will be undefined
        if repo_num:
            self.finish_report()

    def report_page(self, repo_num, repo_name, page_num, page_data):
        "Print out the page data"
        raise NotImplementedError()

    def separator(self):
        "Print out a separator line between repositories"
        raise NotImplementedError()

class RawReport(Report):
    "Print out the raw json"
    def separator(self):
        self.stream.write(",\n")
    def report_page(self, repo_num, repo_name, page_num, page_data):
        self.stream.write(json.dumps(page_data, indent=2))

class BriefReport(Report):
    "Print out a per-line report"
    def separator(self):
        self.stream.write(f"{'='*64}\n")

    def report_page(self, repo_num, repo_name, page_num, page_data):
        for ent in page_data["entries"]:
            version = ent["name"]
            size = hrn(ent["full_size"])
            self.stream.write(f"{repo_name}:{version} ({size})\n")

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

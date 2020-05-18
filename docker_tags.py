#!/usr/bin/env python3
# pylint: disable=bad-continuation,eval-used
"""
docker_tags.py
"""
import os
import sys
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

def repo_url(name, registry=DOCKER_HUB_REGISTRY):
    "Yield each url created from the repo names in 'names'"
    if '/' in name:
        return f"{registry}/v2/repositories/{name}/tags/"
    return f"{registry}/v2/repositories/library/{name}/tags/"

class Report:
    "Base report class"
    _stream = None
    _jsonlog = None
    _text = None
    _json = None

    def __init__(self, **kw):
        self._stream = kw.get("stream") or sys.stdout
        self._jsonlog = open(kw.get("json_log") or os.devnull, "w")

    def start(self):
        "Start the report"
        # Nothing to do normally.

    def finish(self):
        "Do something at the end"
        # Nothing.

    def hub_data(self, repo_name):
        "Iterate the data pages from the given repository"
        url = repo_url(repo_name)
        while url:
            rsp = urllib.request.urlopen(url)
            if not 200 <= rsp.getcode() < 300:
                raise BadResponseStatus(rsp.getcode())
            self._text = rsp.read().decode("utf8")
            self._jsonlog.write(self._text)
            data = json.loads(self._text)
            yield data
            url = data['next']

    def run(self, docker_repos):
        "The main report loop"
        repo_num = 0 # Have to pre-initialize repo_num ...
        for repo_num, repo_name in enumerate(docker_repos):
            if repo_num:
                self.separator()
            else:
                self.start()
            for page_num, page in enumerate(self.hub_data(repo_name)):
                self.report_page(repo_num, repo_name, page_num, page)
        # because if docker_repos is empty then repo_num will be undefined
        if repo_num:
            self.finish()

    def report_page(self, repo_num, repo_name, page_num, page_data):
        "Print out the page data"
        raise NotImplementedError()

    def separator(self):
        "Print out a separator line between repositories"
        raise NotImplementedError()

class RawReport(Report):
    "Print out the raw json"
    def separator(self):
        self._stream.write(",\n")
    def report_page(self, repo_num, repo_name, page_num, page_data):
        self._stream.write(json.dumps(page_data, indent=2))

class BriefReport(Report):
    "Print out a per-line report"
    def separator(self):
        self._stream.write(f"{'='*64}\n")

    def report_page(self, repo_num, repo_name, page_num, page_data):
        for ent in page_data["results"]:
            self.report_line(repo_name, **ent)

    def report_line(self, repo_name, name, full_size, images, **kw):
        "Print out a single line"
        size = hrn(full_size)
        arch = ", ".join(_["architecture"] for _ in images)
        self._stream.write(f"{repo_name}:{name}  {size}  [{arch}]\n")

class DetailedReport(Report):
    "The detailed, verbose report"

REPORT_CLASSES = {
    'brief': BriefReport,
    'raw': RawReport,
    'detailed': DetailedReport
}

def main():
    "Run from the command line"
    from argparse import ArgumentParser, FileType
    agp = ArgumentParser(description=__doc__)
    agp.add_argument("--json", action="store", default=None,
            type=FileType('w'),
            help="Stream received json to this file")
    agp.add_argument("--report", type=str, action="store", default="brief",
            help="Use this report type (brief|raw|detailed)")
    agp.add_argument("images", nargs="+",
            help="Docker images to check")
    args = agp.parse_args()
    cls = REPORT_CLASSES.get(args.report)
    if not cls:
        args.error(f"Unknown report type: {args.report}")
    try:
        cls(json_log=args.json, stream=sys.stdout).run(args.images)
    except KeyboardInterrupt:
        print("")

if __name__ == "__main__":
    main()
# Done.

#!/usr/bin/env python3
# pylint: disable=bad-continuation,eval-used
"""
docker_tags.py
"""
import os
import sys
import json
import urllib.request

from datetime import datetime

DOCKER_HUB_REGISTRY = "https://registry.hub.docker.com"

def hrn(num, magnitude=1024):
    "Human-readable-number"
    if not num:
        return "?"
    if num < magnitude:
        return f"{num:,}B"
    ## Up to PetaBytes should be more than enough.
    for mag in 'KMGTP':
        num, frac = divmod(num, magnitude)
        if num < magnitude:
            return f"{num:,}.{(100*frac//1024):02}{mag}B"
    return f"{num:,}.{(100*frac//1024):02}PB"

def repo_url(name, registry=DOCKER_HUB_REGISTRY):
    "Yield each url created from the repo names in 'names'"
    if '/' in name:
        return f"{registry}/v2/repositories/{name}/tags/"
    return f"{registry}/v2/repositories/library/{name}/tags/"

class Report:
    "Base report class"
    _stream = None
    _jsonlog = None

    def __init__(self, **kw):
        self._stream = kw.get("stream") or sys.stdout
        self._jsonlog = open(kw.get("json_log") or os.devnull, "w")

    def hub_data(self, repo_name):
        "Iterate the data pages from the given repository"
        url = repo_url(repo_name)
        while url:
            rsp = urllib.request.urlopen(url)
            status, body = rsp.getcode(), rsp.read().decode("utf8")
            if not 200 <= status < 300:
                sys.stderr.write(f"[W] Bad http status: {status} [{body}]\n")
                break
            self._jsonlog.writelines([body, "\n"])
            data = json.loads(body)
            yield data
            url = data['next']

    # pylint: disable=no-self-use
    def filter_architectures(self, images, default=None):
        "Return a list of all the supported architectures"
        if images:
            arch1 = [(_["architecture"], _["variant"], _["size"])
                     for _ in images]
            arch2 = [(f"{a}{'/' if v else ''}{v or ''}", s)
                     for a, v, s in arch1]
            return [(a, s) for a, s in arch2 if a not in EXCEPT_ARCH]
        return default

    def run(self, docker_repos):
        "The main report loop"
        repo_num = 0 # Have to pre-initialize repo_num ...
        for repo_num, repo_name in enumerate(docker_repos):
            if repo_num:
                self.page_separator()
            else:
                self.start()
            for page_num, page in enumerate(self.hub_data(repo_name)):
                self.page_heading(repo_num, repo_name, page_num, page)
                self.page_content(repo_num, repo_name, page_num, page)
        # because if docker_repos is empty then repo_num will be undefined
        if repo_num:
            self.finish()

    def start(self):
        "Start the report"
        # Nothing to do normally.

    def finish(self):
        "Do something at the end"
        # Nothing.

    def page_separator(self):
        "Print out a separator line between repositories"
        # Do nothing

    def page_heading(self, repo_num, repo_name, page_num, page_data):
        "Display a page heading before its data?"
        # but nothing

    def page_content(self, repo_num, repo_name, page_num, page_data):
        "Print out the page data"
        # Empty by default

    def page_bottom(self, repo_num, repo_name, page_num, page_data):
        "Print out at the bottom of the page"
        # Empty by default

    def content_line(self, repo_name, **_):
        "Print out a single line"
        # Empty by default

class RawReport(Report):
    "Print out the raw json"
    def page_content(self, repo_num, repo_name, page_num, page_data):
        self._stream.write(json.dumps(page_data, indent=2))

class BriefReport(Report):
    "Print out a per-line report"
    def page_separator(self):
        # Print out a line between repositories
        self._stream.write(f"{'='*64}\n")

    def page_content(self, repo_num, repo_name, page_num, page_data):
        for ent in page_data["results"]:
            self.content_line(repo_name, **ent)

    # pylint: disable=arguments-differ
    def content_line(self, repo_name, name, full_size, **_):
        size = hrn(full_size)
        archs = self.filter_architectures(_["images"], [("x86_64", full_size)])
        alst = ", ".join(a for a, s in sorted(archs))
        self._stream.write(f"{repo_name}:{name}  {size}  [{alst}]\n")

class DetailedReport(BriefReport):
    "The detailed, verbose report"
    # pylint: disable=arguments-differ
    def content_line(self, repo_name, name, full_size, last_updated, **_):
        wrt = self._stream.write
        if last_updated:
            try:
                upddt = datetime.strptime(last_updated, "%Y-%m-%dT%H:%M:%S.%fZ")
                last_updated = f" ({upddt.ctime()})"
            except ValueError:
                upddt = last_updated = ""
        wrt(f"{repo_name}:{name}{last_updated}\n")
        archs = self.filter_architectures(_["images"], [("x86_64", full_size)])
        for arch, size in sorted(archs):
            wrt(f"  {arch}  {hrn(size)}\n")
        wrt("\n")

REPORT_CLASSES = {
    'brief': BriefReport,
    'raw': RawReport,
    'detailed': DetailedReport
}

EXCEPT_ARCH = {"386", "arm/v7", "ppc64le", "s390x"}

def main():
    "Run from the command line"
    from argparse import ArgumentParser, FileType
    agp = ArgumentParser(description=__doc__)
    agp.add_argument("--json", action="store", default=None,
            type=FileType('w'),
            help="Stream received json to this file")
    agp.add_argument("--all-arch", action="store_true", default=False,
            help="Don't omit the uncommon architectures")
    agp.add_argument("--report", type=str, action="store", default="brief",
            help="Use this report type (brief|raw|detailed)")
    agp.add_argument("images", nargs="+",
            help="Docker images to check")
    args = agp.parse_args()
    cls = REPORT_CLASSES.get(args.report)
    if not cls:
        args.error(f"Unknown report type: {args.report}")
    if args.all_arch:
        sys.stderr.write("Displaying all architectures\n")
        EXCEPT_ARCH.clear()
    else:
        _ = ", ".join(EXCEPT_ARCH)
        sys.stderr.write(f"Omitting these architectures: {_}\n")
    try:
        cls(json_log=args.json, stream=sys.stdout).run(args.images)
    except KeyboardInterrupt:
        print("")

if __name__ == "__main__":
    main()
# Done.

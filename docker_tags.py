#!/usr/bin/env python3
# pylint: disable=bad-continuation,eval-used
"""
Query the public docker hub for available versions
of one or more repositories.
"""

__author__ = "Gustavo Cordova Avila"
__version__ = '1.0'

import os
import sys
import json
import urllib.request

from datetime import datetime as dt

DOCKER_HUB_REGISTRY = "https://registry.hub.docker.com"
EXCEPT_ARCH = {"386", "arm/v5", "arm/v6", "arm/v7", "ppc64le", "s390x"}

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

def hub_data(repo_name):
    "Iterate the data pages from the given repository"
    url = repo_url(repo_name)
    while url:
        rsp = urllib.request.urlopen(url)
        status, body = rsp.getcode(), rsp.read().decode("utf8")
        if not 200 <= status < 300:
            sys.stderr.write(f"[W] Bad http status: {status} [{body}]\n")
            break
        data = json.loads(body)
        yield data
        url = data["next"]

class Report:
    "Base report class"
    _stream = None

    def __init__(self, **kw):
        self._stream = kw.get("stream") or sys.stdout

    def run(self, docker_repos):
        "The main report loop"
        repo_num = None # Have to pre-initialize repo_num ...
        for repo_num, repo_name in enumerate(docker_repos):
            if repo_num:
                self.page_separator()
            else:
                self.start()
            for page_num, page in enumerate(hub_data(repo_name)):
                self.page_heading(repo_num, repo_name, page_num, page)
                self.page_content(repo_num, repo_name, page_num, page)
                self.page_bottom(repo_num, repo_name, page_num, page)
        # because if docker_repos is empty then repo_num will be undefined
        if repo_num is not None:
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
    "Emit the json content as it's received from the Docker API"
    def page_content(self, repo_num, repo_name, page_num, page_data):
        self._stream.write(json.dumps(page_data, indent=2))

class JsReport(Report):
    "Stream the received json into a single valid document"
    def start(self):
        self._stream.write("{")

    def page_content(self, repo_num, repo_name, page_num, page_data):
        from json import dumps
        if page_num == 0:
            self._stream.writelines([
                f'"count":{page_data["count"]},',
                '"results":['])
        sub_doc = []
        for nth, _ in enumerate(page_data["results"]):
            sub_doc.append("," if nth else "")
            sub_doc.append(dumps(_, indent=None, separators=(',', ':')))
        self._stream.writelines(sub_doc)

    def finish(self):
        self._stream.write("]}")

def architectures(docker_images):
    "Return a (id, (arch, variant, os, os_v, size)) dict from the images"
    def xid(architecture, variant, os, os_version, size, **_):
        "Return the short id for an architecture"
        arch_id = \
            f'{architecture}'+(f'/{variant}' if variant else '') \
            + (f':{os[0].upper()}' if os else '') \
            + (f'-{os_version.split(".")[0]}' if os_version else '')
        return arch_id, (architecture, variant, os, os_version, size)
    arch = (xid(**_) for _ in docker_images)
    return {k: v for k,v in arch if k not in EXCEPT_ARCH}

class BriefReport(Report):
    "Print out a terse report with one record per line"
    def page_separator(self):
        # Print out a line between repositories
        self._stream.write(f"{'='*64}\n")

    def page_content(self, repo_num, repo_name, page_num, page_data):
        for ent in page_data["results"]:
            self.content_line(repo_name, **ent)

    # pylint: disable=arguments-differ
    def content_line(self, repo_name, name, full_size, images, **_):
        archs = sorted(architectures(images).keys() or ["x86_64"])
        self._stream.write(
            f"{repo_name}:{name} {hrn(full_size)} [{', '.join(archs)}]\n")

class DetailedReport(BriefReport):
    "A more detailed report"
    # pylint: disable=arguments-differ
    def content_line(self, repo_name, name, full_size, last_updated, **_):
        wrt = self._stream.write
        if last_updated:
            try:
                upddt = dt.strptime(last_updated, "%Y-%m-%dT%H:%M:%S.%fZ")
                last_updated = f" ({upddt.ctime()})"
            except ValueError:
                upddt = last_updated = ""
        wrt(f"{repo_name}:{name}{last_updated}\n")
        archs = architectures(_["images"])
        if archs:
            for xid, (nm, vr, os, osv, sz) in sorted(archs.items()):
                vr = f"/{vr}" if vr else ''
                os = f" {os}" if os else ''
                osv = f"-{osv}" if os and osv else ''
                wrt(f"  {nm}{vr}{os}{osv} {hrn(sz)}\n")
        else:
            wrt(f"  Linux/x86_64 {hrn(full_size)}\n")
        wrt("\n")

REPORT_CLASSES = {
    'brief': BriefReport,
    'raw': RawReport,
    'js': JsReport,
    'detailed': DetailedReport
}

def main():
    "Run from the command line"
    from argparse import ArgumentParser
    agp = ArgumentParser(description=__doc__)
    _ = ", ".join(sorted(EXCEPT_ARCH))
    agp.add_argument("--all",
            action="store_true", default=False,
            help=f"Don't omit any architectures ({_})")
    _ = "|".join(sorted(REPORT_CLASSES))
    agp.add_argument("--report",
            action="store", type=str, default="brief",
            help=f"Set the report type to use ({_})")
    agp.add_argument("images",
            action="store", type=str, nargs="+",
            help="Docker images to check")
    args = agp.parse_args()
    cls = REPORT_CLASSES.get(args.report)
    if not cls:
        args.error(f"Unknown report type: {args.report}")
    if args.all:
        sys.stderr.write("Displaying all architectures\n")
        EXCEPT_ARCH.clear()
    else:
        _ = ", ".join(EXCEPT_ARCH)
        sys.stderr.write(f"Omitting these architectures: {_}\n")
    try:
        cls(stream=sys.stdout).run(args.images)
    except KeyboardInterrupt:
        print("")

if __name__ == "__main__":
    main()
# Done.

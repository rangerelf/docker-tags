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

def get(url, log_json=None):
    "Iterate the data pages from the given url"
    while url:
        rsp = urllib.request.urlopen(url)
        if not 200 <= rsp.getcode() < 300:
            raise BadResponseStatus(rsp.getcode())
        text = rsp.read()
        if log_json:
            log_json.write(text.decode('utf8'))
        data = json.loads(text)
        yield data
        url = data['next']

def repo_url(name, registry=DOCKER_HUB_REGISTRY):
    "Yield each url created from the repo names in 'names'"
    prefix = f"{registry}/v2/repositories"
    if '/' in name:
        return f"{prefix}/{name}/tags/"
    return f"{prefix}/library/{name}/tags/"

def compile_template(template):
    "Return a code object to run the template"
    prefix, template = template.split(":", 1)
    if prefix == 'D':
        co_o = compile(f'''f"{template}"''', '<template>', 'eval')
        def template_func(page, _vars):
            "Run the template code in the context of the page"
            return eval(co_o, {**globals(), **_vars}, page)
    elif prefix == 'L':
        co_o = compile(f'''(f"{template}")''', '<template>', 'eval')
        def template_func(page, _vars):
            "Run the template code in the context of the result line"
            base_ns = {**globals(), **_vars}
            return "\n".join(eval(co_o, {**base_ns, **_})
                             for _ in page["results"])
    else:
        raise ValueError(f"Unknown template prefix: {prefix}")
    return template_func

def run_report(docker_repos, **kwarg):
    "Report versions of images found in 'docker_repositories'"
    jsl = kwarg.get('json_log')
    tmpl_f = compile_template(kwarg.get('template'))
    try:
        for repository_name in docker_repos:
            for page in get(repo_url(repository_name), log_json=jsl):
                report_page = tmpl_f(page, locals())
                print(report_page)
    except KeyboardInterrupt:
        print("")

# Dictionary of callables with the format.
TEMPLATES = {
    'short': "L:{repository_name}:{name} ({hrn(full_size)})",
    'raw': "D:json.dumps(page, indent=2)"
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

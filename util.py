WHITESPACE = '\r\n\t '


def get_arg(template, name):
    if (arg := template.get_arg(name)) is not None:
        return arg.value.strip(WHITESPACE)


def get_category_pageids(site, cmtitle):
    for r in site.query(list='categorymembers', cmtitle=cmtitle, cmtype='page'):
        for page in r['categorymembers']:
            yield page['pageid']


def get_character_page(site, name):
    for r in site.query(prop='revisions', titles=[name], rvprop=['ids', 'content'], rvslots='*'):
        return r['pages'][0]


def get_templates(parsed, name):
    for template in parsed.templates:
        if template.normal_name() == name:
            yield template


def iter_category(site, cmtitle):
    return iter_pages(site, list(get_category_pageids(site, cmtitle)))


def iter_pages(site, pageids):
    for r in site.query(prop='revisions', pageids=pageids, rvprop=['ids', 'content'], rvslots='*'):
        for page in r['pages']:
            yield page

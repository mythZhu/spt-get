#!/usr/bin/python -tt
# vim: sw=4 ts=4 sts=4 et ai

import os
import sys
import gzip
import Queue
import threading
from urlparse import urljoin
from xml.etree import cElementTree as ET

import msger
from urlfetch import fetch_url
from pkgquery import PackageQuery

def parse_with_ns(xmlfile):
    events = "start", "start-ns"
    root = None
    ns = {}
    for event, elem in ET.iterparse(xmlfile, events):
        if event == "start-ns":
            if elem[0] in ns and ns[elem[0]] != elem[1]:
                raise KeyError("Duplicate prefix with different URI found.")
            ns[elem[0]] = "{%s}" % elem[1]
        elif event == "start":
            if root is None:
                root = elem
    return ET.ElementTree(root), ns

def locate_primary(repository):
    metadata_url = urljoin(repository, 'repodata/repomd.xml')
    metadata_path = fetch_url(metadata_url)
    metadata_file, ns = parse_with_ns(metadata_path)
    root = metadata_file.getroot()

    for data_element in root.findall(ns[''] + 'data'):
        if data_element.get("type") == "primary":
            location_element = data_element.find(ns[''] + 'location')
            primary_path = location_element.get('href')
            break
    else:
        raise IOError("'%s' contains no primary location" % metadata_path)

    os.unlink(metadata_path)
    return urljoin(repository, primary_path)

def parse_metadata(repository):
    primary_url = locate_primary(repository)
    primary_path = fetch_url(primary_url)
    unzipped_primary = gzip.GzipFile(primary_path)
    primary_file, ns = parse_with_ns(unzipped_primary)
    root = primary_file.getroot()

    whois = {}
    queries = {}
    for element in root.findall(ns[''] + 'package'):
        query = PackageQuery(element)
        queries[query.fullname] = query
        provides = [query.fullname]
        provides.extend([ entry for entry, flags, version in query.provides])
        provides.extend(query.files)
        for pro in set(provides):
            whois.setdefault(pro, []).append(query.fullname)

    os.unlink(primary_path)
    return whois, queries

def resolve_deps(repository, wants):
    needs = Queue.Queue(0)
    resolver = ResolveWorker(repository, wants, needs, quiet=False)
    resolver.setDaemon(True)
    resolver.start()
    resolver.join()
    result = []
    while True:
        try:
           result.append(needs.get(block=False)) 
        except Queue.Empty:
            break
    return result

class ResolveWorker(threading.Thread):
    def __init__(self, repository, wants, needs, quiet=True):
        super(ResolveWorker, self).__init__()
        self.__repository = repository
        self.__wants = wants
        self.__needs = needs
        self.__quiet = quiet

    def __resolve_adjs(self, node, whois, queries):
        adjacents = []
        for entry, flags, version in node.requires:
            candidates = [ queries[e] for e in whois[entry] ]
            if flags == 'LE':
                adjacents.extend([ c for c in candidates if c <= version ])
            elif flags == 'EQ':
                adjacents.extend([ c for c in candidates if c == version ])
            elif flags == 'GE':
                adjacents.extend([ c for c in candidates if c >= version ])
            else:
                adjacents.append(candidates[0])

        return adjacents

    def __resolve_deps(self, wants, whois, queries):
        nodes = []
        visit = {}
        for want in wants:
            try:
                node = queries[whois[want][0]]
            except KeyError:
                msger.error("package '%s' not found" % want)
                sys.exit(1)
            else:
                nodes.append(node)
        for node in nodes:
            visit[node.fullname] = node
            self.__quiet or \
            msger.info("--> %s set to be installed"  % node.fullname)

        while nodes:
            parent = nodes.pop(0)
            children = self.__resolve_adjs(parent, whois, queries)
            for child in children:
                if visit.get(child.fullname): continue
                visit[child.fullname] = child
                nodes.append(child)
                self.__quiet or \
                msger.info("--> %s set to be installed"  % child.fullname)

        packages = []
        for node in visit.values():
            packages.append(node.location)

        return packages

    def run(self):
        whois, queries = parse_metadata(self.__repository)
        pkgs_href = self.__resolve_deps(self.__wants, whois, queries)
        for pkg_href in pkgs_href:
            pkg_url = urljoin(self.__repository, pkg_href)
            self.__needs.put(pkg_url, block=False)

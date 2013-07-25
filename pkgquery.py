#!/usr/bin/python -tt
# vim: sw=4 ts=4 sts=4 et ai

from xml.etree import cElementTree as ET

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

class PackageQuery(object):

    __xmlns = { ''     : '{http://linux.duke.edu/metadata/common}',
                'suse' : '{http://novell.com/package/metadata/suse/common}',
                'rpm'  : '{http://linux.duke.edu/metadata/rpm}'
              }

    def __init__(self, element):
        self.__element = element

    def __cmp__(self, other):
        lh = "%s-%s" % (self.version, self.release)
        if hasattr(other, 'version') and hasattr(other, 'release'):
            rh = "%s-%s" % (other.version, other.release)
        else:
            rh = other
        if lh < rh: return -1
        if lh == rh: return 0
        if lh > rh: return 1

    def __versionElement(self):
        return self.__element.find(self.__xmlns[''] + 'version')

    def __formatElement(self):
        return self.__element.find(self.__xmlns[''] + 'format')

    def __parseEntry(self, element):
        entry = element.get('name')
        flags = element.get('flags')
        version = ''

        if flags:
            version = element.get('ver')
            release = element.get('rel')
            if release:
                version += "-%s" % release

        return (entry, flags, version)

    def __parseEntryCollection(self, collection):
        format_element = self.__formatElement()
        collection_element = format_element.find(collection)

        entries = []
        for entry_element in collection_element.findall(self.__xmlns['rpm'] + 'entry'):
            entry = self.__parseEntry(entry_element)
            entries.append(entry)

        return entries

    @property
    def name(self):
        name_element = self.__element.find(self.__xmlns[''] + 'name')
        return name_element.text
    
    @property
    def fullname(self):
        return "%s-%s-%s.%s" % (self.name, self.version, 
                                self.release, self.arch)

    @property
    def arch(self):
        arch_element = self.__element.find(self.__xmlns[''] + 'arch')
        return arch_element.text

    @property
    def epoch(self):
        return self.__versionElement().get('epoch')

    @property
    def version(self):
        return self.__versionElement().get('ver')

    @property
    def release(self):
        return self.__versionElement().get('rel')

    @property
    def location(self):
        location_element = self.__element.find(self.__xmlns[''] + 'location')
        return location_element.get('href')

    @property
    def requires(self):
        try:
            return self.__parseEntryCollection(self.__xmlns['rpm'] + 'requires')
        except:
            return []

    @property
    def provides(self):
        return self.__parseEntryCollection(self.__xmlns['rpm'] + 'provides')

    @property
    def files(self):
        format_element = self.__formatElement()
        file_elements = format_element.findall(self.__xmlns[''] + 'file')

        entries = []
        for file_element in file_elements:
            entries.append(file_element.text)

        return entries

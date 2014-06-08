# -*- coding: utf-8 -*-
#
#  match.py
#  
#  Copyright 2013-2014 David Reed <david@ktema.org>
#  This file is available under the terms of the MIT License.
#

from difflib import SequenceMatcher
from operator import itemgetter

COMPARE_EXACT = "exact"
COMPARE_PREFIX = "prefix"
COMPARE_FUZZY = "fuzzy"

class Result(object):
    def __init__(self, incoming, master, score):
        self.incoming = incoming
        self.master = master
        self.score = score
        
class Mapping(object):
    def __init__(self, incoming_key, master_key, compare=COMPARE_EXACT, points=1, strip=True):
        self.key = incoming_key
        self.master_key = master_key
        self.compare = compare
        self.points = points
        self.strip = strip
    
    def compare_records(self, master, incoming):
        if self.master_key not in master.values or self.key not in incoming.values:
            raise Exception, "Mapping {} specifies a key that does not exist in one or more records.".format(self)
        
        master_value = master.values[self.master_key].strip().strip("\"'") if self.strip else master.values[self.master_key]
        incoming_value = incoming.values[self.key].strip().strip("\"'") if self.strip else incoming.values[self.key]        
        if self.compare == COMPARE_EXACT:
            if master_value == incoming_value:
                return self.points
        elif self.compare == COMPARE_PREFIX:
            if master_value.startswith(incoming_value) or incoming_value.startswith(master_value):
                return self.points
        elif self.compare == COMPARE_FUZZY:
            ratio = SequenceMatcher(None, master_value, incoming_value).ratio()
            # FIXME: this is simplistic. We should have a cutoff value
            return self.points * ratio
        else:
            return 0
            
class Profile(object):
    def __init__(self, **kwargs):
        if kwargs.get("mappings"):
            self.mappings = kwargs["mappings"]
        elif kwargs.get("source"):
            self.mappings = self.__parse_source(kwargs["source"])
        else:
            self.mappings = []
            
    def __parse_source(self, source):
        maps = []
    
        for record in source.records():
            if record.values["compare"] == "exact":
                compare = COMPARE_EXACT
            elif record.values["compare"] == "prefix":
                compare = COMPARE_PREFIX
            elif record.values["compare"] == "fuzzy":
                compare = COMPARE_FUZZY
            else:
                raise Exception, "Invalid compare type {} in profile.".format(record.values["compare"])
        
            maps.append(Mapping(record.values["key"],
                                record.values["master-key"],
                                compare,
                                int(record.values["points"]),
                                bool(record.values["strip"])))
                                
        return maps

    def compare_records(self, master, incoming):
        return sum([mapping.compare_records(master, incoming) for mapping in self.mappings])
        
    def compare_sources(self, master, incoming, cutoff = 0):
        results = []
        
        for (index, incoming_record) in enumerate(incoming.records()):
            for master_record in master.records():
                points = self.compare_records(master_record, incoming_record)
                if points >= cutoff:
                    results.append(Result(incoming_record, master_record, points))
                    
        return results
    

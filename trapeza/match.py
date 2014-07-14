# -*- coding: utf-8 -*-
#
#  match.py
#  
#  Copyright 2013-2014 David Reed <david@ktema.org>
#  This file is available under the terms of the MIT License.
#

import nilsimsa
from operator import itemgetter

__all__ = ["COMPARE_EXACT", "COMPARE_PREFIX", "COMPARE_FUZZY", "ProcessedSource", "Result", "Mapping", "Profile"]

COMPARE_EXACT = u"exact"
COMPARE_PREFIX = u"prefix"
COMPARE_FUZZY = u"fuzzy"

class AdditiveDict(dict):            
    def append(key, value):
        self.setdefault(key, []).append(value)     


class ProcessedSource(object):
    
    NILSIMSA_DISTANCE_BASE = nilsimsa.Nilsimsa(u"b4se str1ng 4 c0mparison with NILSIMSA hash!".encode("utf-8")).digest()
    
    def __init__(self, source, master = True, profile = None):
        self.source = source
        self.master = master
        self.profile = profile
        self.processed = False
    
    def process(self):
        self.exact = {}
        self.prefix = {}
        self.fuzzy = {}
        
        exact_keys = []
        prefix_keys = []
        fuzzy_keys = []
        
        if self.profile is not None:
            for mapping in self.profile.mappings:
                if mapping.compare == COMPARE_EXACT:
                    exact_keys.append(mapping.master_key if self.master else mapping.key)
                elif mapping.compare == COMPARE_FUZZY:
                    fuzzy_keys.append(mapping.master_key if self.master else mapping.key)
                elif mapping.compare == COMPARE_PREFIX:
                    prefix_keys.append(mapping.master_key if self.master else mapping.key)
        else:
            exact_keys = prefix_keys = fuzzy_keys = source.headers()
            
        for key in exact_keys:
            self.exact[key] = AdditiveDict()
        for key in prefix_keys:
            self.prefix[key] = AdditiveDict()
        for key in fuzzy_keys:
            self.fuzzy[key] = AdditiveDict()
            
        for record in self.source.records():
            for key in exact_keys:
                self.exact[key].append(record.values[key], record)
            
            for key in prefix_keys:
                val = record.values[key]
                
                if len(val) > self.profile.prefix_len:
                    for i in range(0, len(val)-self.profile.prefix_len, -1):
                        self.prefix[key].append(val[:i], record)
                        
            for key in fuzzy_keys:
                n = nilsimsa.Nilsimsa(record.values[key].encode("utf-8"))
                self.fuzzy[key].append(n.compare(ProcessedSource.NILSIMSA_DISTANCE_BASE), (n.digest(), record))
                
        self.processed = True

        
    def matches(self, mapping, record):
        if not self.processed:
            raise Exception("Please process this source before attempting a match.")
        
        key = mapping.master_key if self.master else mapping.key
        value = record.values[mapping.master_key if not self.master else mapping.key]
        
        results = []
        
        if mapping.compare == COMPARE_EXACT:
            results.extend(self.exact[key].get(value, []))
        elif mapping.compare == COMPARE_PREFIX:
            if len(value) > self.profile.prefix_len:
                other_has_this_prefix = self.prefix[key].get(value, [])
                
                results.extend(other_has_this_prefix)
                
                for i in range(self.profile.prefix_len, len(value)-1):
                    results.extend(self.prefix[key].get(value[:i], []))
                    
        elif mapping.compare == COMPARE_FUZZY:
            nilsimsa_distance = nilsimsa.Nilsimsa(value.encode("utf-8")).compare(ProcessedSource.NILSIMSA_DISTANCE_BASE)
            results.extend(self.fuzzy[key].get(nilsimsa_distance, []))
            
        return results
            

class Result(object):
    def __init__(self, incoming, master, score):
        self.incoming = incoming
        self.master = master
        self.score = score
        
class Mapping(object):
    def __init__(self, incoming_key, master_key, compare=COMPARE_EXACT, points=1, strip=True, prefix_len = 3):
        self.key = incoming_key
        self.master_key = master_key
        self.compare = compare
        self.points = points
        self.strip = strip
        self.prefix_len = prefix_len
        
    def __str__(self):
    	return "trapeza.Mapping: {0} to {1} using comparison {2} for {3} points.".format(self.key, self.master_key, self.compare, self.points)
    
    def compare_records(self, master, incoming):
        if self.master_key not in master.values or self.key not in incoming.values:
            raise Exception, "Mapping {0} specifies a key that does not exist in one or more records.".format(self)
        
        master_value = master.values[self.master_key].strip().strip("\"'") if self.strip else master.values[self.master_key]
        incoming_value = incoming.values[self.key].strip().strip("\"'") if self.strip else incoming.values[self.key]
        
        if len(master_value) == 0 or len(incoming_value) == 0:
        	return 0
            
        if self.compare == COMPARE_EXACT:
            if master_value == incoming_value:
                return self.points
        elif self.compare == COMPARE_PREFIX:
            if (master_value.startswith(incoming_value) and len(incoming_value) > self.prefix_len) \
                or (incoming_value.startswith(master_value) and len(master_value) > self.prefix_len):
                return self.points
        elif self.compare == COMPARE_FUZZY:
            return ((nilsimsa.Nilsimsa(master_value.encode("utf-8")).compare(nilsimsa.Nilsimsa(incoming_value.encode("utf-8")).digest()) + 127) / 255.0) * self.points
        
        return 0
            
class Profile(object):
    prefix_len = 3
    
    def __init__(self, **kwargs):
        if kwargs.get("mappings"):
            self.mappings = kwargs["mappings"]
        elif kwargs.get("source"):
            self.mappings = self.__parse_source(kwargs["source"])
        else:
            self.mappings = []
    
    def __str__(self):
    	return "trapeza.Profile with mappings: {}.".format(self.mappings)
    
    def __parse_source(self, source):
        maps = []
    
        for record in source.records():
            if record.values[u"compare"] == u"exact":
                compare = COMPARE_EXACT
            elif record.values[u"compare"] == u"prefix":
                compare = COMPARE_PREFIX
            elif record.values[u"compare"] == u"fuzzy":
                compare = COMPARE_FUZZY
            else:
                raise Exception, "Invalid compare type {} in profile.".format(record.values[u"compare"])
        
            maps.append(Mapping(record.values[u"key"],
                                record.values[u"master-key"],
                                compare,
                                int(record.values[u"points"]),
                                bool(record.values[u"strip"])))
                                
        return maps

    def compare_records(self, master, incoming):
        return sum([mapping.compare_records(master, incoming) for mapping in self.mappings])
        
    def compare_sources(self, master, incoming, cutoff = 0):
        if isinstance(master, ProcessedSource):
            return self._compare_sources_processed(master, incoming, cutoff)
            
        results = []
        
        for incoming_record in incoming.records():
            for master_record in master.records():
                points = self.compare_records(master_record, incoming_record)
                if points >= cutoff:
                    results.append(Result(incoming_record, master_record, points))
                    
        return results
    
    def _compare_sources_processed(self, master, incoming, cutoff = 0):
        if not master.processed or master.profile not in [self, None]:
            raise Exception("Cannot compare using an unprocessed source or a source processed with the wrong profile.")
            
        results = []
        
        for record in incoming.records():
            results_this_record = {}
            
            for mapping in self.mappings:
                for master_record in master.matches(mapping, record):
                    if mapping.compare == COMPARE_EXACT or mapping.compare == COMPARE_PREFIX:
                        score = results_this_record.get(master_record, 0)
                        results_this_record[master_record] = score + mapping.points
                    else:
                        # for Nilsimsa results the "record" is actually a (digest, record) tuple
                        (digest, real_record) = master_record
                        score = results_this_record.get(real_record, 0)
                        value = real_record.values[mapping.master_key]
                        results_this_record[real_record] = score + _nilsimsa_ratio_as_percent(digest, nilsimsa.Nilsimsa(value.encode("utf-8"))) * mapping.points
                        
            for each_result_key in results_this_record:
                results.append(Result(record, each_result_key, results_this_record[each_result_key]))
        
        return results
                
def _nilsimsa_ratio_as_percent(digest1, nilsimsa_obj):
    return (nilsimsa_obj.compare(digest1) + 127) / 255.0

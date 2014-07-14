# -*- coding: utf-8 -*-
#
#  trapeza.py
#  
#  Copyright 2013-2014 David Reed <david@ktema.org>
#  This file is available under the terms of the MIT License.
#

import os, csv, itertools, formats

__all__ = ["Record", "Source", "get_format", "load_source", "sources_consistent", "unify_sources", "write_source"]

class Record(object):
    def __init__(self, values, primary_key = None, input_line = None):
        self.values = values
        self.primary_key = primary_key
        self.input_line = input_line
        
    def __eq__(self, other):
        if other is not None and isinstance(other, Record):
            if self.record_id() is not None and other.record_id() is not None:
                return self.record_id() == other.record_id()
            else:
                return self.values == other.values
        
        return False
            
    def __str__(self):
        return str(self.values)
                    
    def record_id(self):
        if self.primary_key:
            return self.values[self.primary_key]
        
        return None
        
    def input_line(self):
        return self.input_line
    
    def set_input_line(self, input_line):
        self.input_line = input_line
        

class Source(object):
    def __init__(self, headers = [], primary_key = None):
        self.__records = []
        self.__headers = headers
        self.__primary_key = primary_key
        self.__index = {}
        
    def records(self):
        return self.__records
        
    def headers(self):
        return self.__headers
    
    def primary_key(self):
        return self.__primary_key
    
    def set_primary_key(self, primary_key):
        if primary_key is None or primary_key in self.headers():
            self.__primary_key = primary_key
            for record in self.__records:
                record.primary_key = primary_key
            self.__rebuild_index()
        else:
            raise Exception("Primary key {} does not exist in source.", primary_key)
        
    def __rebuild_index(self):
        self.__index = {}
        
        if self.primary_key():
            for record in self.records():
                if record.record_id() in self.__index:
                    raise Exception("Source contains records with the same primary key.")
            
                if record.record_id() is None:
                    raise Exception("Record {} is missing the primary key {}.".format(record, self.primary_key()))
        
                self.__index[record.record_id()] = record

    def add_column(self, column, default_value="", index=None):
        if index is None or index >= len(self.__headers):
            self.__headers.append(column)
        else:
            self.__headers.insert(index, column)
            
        for record in self.__records:
            record.values[column] = default_value
        
    def drop_column(self, column):
        if column != self.__primary_key:
            self.__headers.remove(column)
            for record in self.__records:            
                del record.values[column]
        else:
            raise Exception("Cannot remove the column containing the primary key.")
    
    def drop_column_index(self, column_index):
        self.drop_column(self.__headers[index])
    
    def get_record_with_id(self, key):
        return self.__index.get(key)
            
    def add_record(self, record, index=None):
        if self.primary_key():
            if record.values[self.primary_key()] in self.__index:
                raise Exception("Cannot insert a record whose primary key already exists.")
            else:
                if not self.primary_key() in record.values:
                    raise Exception("Record {} is missing the primary key {}.".format(record, self.primary_key()))
                
                self.__index[record.values[self.primary_key()]] = record
        
        if index is None:
            self.__records.append(record)
        else:
            self.__records.insert(index, record)
            
        record.primary_key = self.primary_key()
    
    def del_record(self, record):
        if self.primary_key():
            self.del_record_with_id(record.values[self.primary_key()])
        else:
            self.filter_records(lambda rec: rec != record)
            
    def del_record_with_id(self, key):
        if self.primary_key() and self.get_record_with_id(key):
            self.filter_records(lambda rec: rec.values[self.primary_key()] != key)
            
    def filter_records(self, func):
        self.__records = filter(func, self.__records)
        if self.primary_key():
            self.__rebuild_index()
        
    def sort_records(self, sortkeys):
        # sorts are stable. Sort in reverse priority order to get a properly sorted list.

        for (key, ascending, value_type) in reversed(sortkeys):
             self.__records.sort(key=lambda rec: float(rec.values[key]) if value_type == "number" else rec.values[key], reverse=not ascending)
            
    def contains_record(self, record):
        if record.record_id() is not None:
            return self.__index.get(record.record_id())
        else:
            return record in self.__records 

def get_format(path, default = "csv"):
    try:
        ext = os.path.splitext(path)[1][1:]
    except:
        return default
    
    if len(ext) > 0:
        return ext.lower()
                
    return default

def load_source(infile, filetype, sheet_name = None, encoding = "utf-8"):
    if len(formats.importers_for_format(filetype)) == 0:
        raise Exception, "No importer available for file {} (type {}).\n".format(infile.name, filetype)
    
    return formats.importers_for_format(filetype)[0]().read(infile, filetype, sheet_name, encoding)
    
def write_source(source, outfile, sheet_name = None, encoding = "utf-8"):
    if len(formats.importers_for_format(filetype)) == 0:
        raise Exception("No exporter available for format {}.".format(filetype))
        
    formats.exporters_for_format(filetype)[0]().write(source, outfile, filetype, sheet_name, encoding)

def sources_consistent(sources):
    first = set(sources[0].headers())

    for source in sources[1:]:
        if set(source.headers()) != first:
            return False
    
    return True
    
def unify_sources(sources):
    totality = set([header for source in sources for header in source.headers()])

    for source in sources:
        for header in totality:
            if header not in source.headers():
                source.add_column(header)

    return sources

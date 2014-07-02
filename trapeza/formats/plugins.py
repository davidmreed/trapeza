# -*- coding: utf-8 -*-
#
#  trapeza/formats/plugins.py
#  
#  Copyright 2013-2014 David Reed <david@ktema.org>
#  This file is available under the terms of the MIT License.
#  

__all__ = ["Importer", "Exporter", "importers_for_format", "exporters_for_format", "available_output_formats", "available_input_formats"]

_importer_registry = {}
_exporter_registry = {}

def register_importer(cls, formats):
    for each_format in formats:
        if not _importer_registry.get(each_format):
            _importer_registry[each_format] = []
            
        _importer_registry[each_format].append(cls)
        
def register_exporter(cls, formats):
    for each_format in formats:
        if not _exporter_registry.get(each_format):
            _exporter_registry[each_format] = []
            
        _exporter_registry[each_format].append(cls)


def available_input_formats():
    return _importer_registry.keys()
    
def available_output_formats():
    return _exporter_registry.keys()

def importers_for_format(a_format):
    return _importer_registry.get(a_format) or []
    
def exporters_for_format(a_format):
    return _exporter_registry.get(a_format) or []

class Importer(object):
    
    formats = []
    
    class __metaclass__(type):
        def __init__(cls, name, bases, dict):
            type.__init__(cls, name, bases, dict)
            register_importer(cls, dict["formats"])
                            
    def read(self, file_like_object, file_format, sheet_name = None):
        raise NotImplementedError
    

class Exporter(object):
    
    formats = []
    
    class __metaclass__(type):
        def __init__(cls, name, bases, dict):
            type.__init__(cls, name, bases, dict)

            register_exporter(cls, dict["formats"])
            
    def write(self, source, file_like_object, file_format, sheet_name = None):
        raise NotImplementedError
    


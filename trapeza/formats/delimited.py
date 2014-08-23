# -*- coding: utf-8 -*-
#
#  trapeza/formats/delimited.py
#  
#  Copyright 2013-2014 David Reed <david@ktema.org>
#  This file is available under the terms of the MIT License.

import csv, trapeza, plugins, io

__all__ = [ "DelimitedImporter", "DelimitedExporter" ]


class DelimitedImporter(plugins.Importer):
    formats = ["csv", "tsv", "chr"]

    def read(self, file_like_object, file_format = "csv", sheet_name = None, encoding = "utf-8"):
        data = file_like_object.read()
        
        if encoding != "utf-8":
            # Python's csv module is (mostly) 8-bit clean and will deal with UTF-8
            data = data.decode(encoding).encode("utf-8")
                    
        # However, it chokes on mixed/foreign newlines (which Excel is prone to outputting).
        # Use .splitlines() to address this
        reader = csv.DictReader(data.splitlines(), dialect=("excel" if file_format == "csv" else "excel-tab"))
        source = trapeza.Source([fieldname.decode("utf-8") for fieldname in reader.fieldnames])
    
        for (index, rec) in enumerate(reader):
            source.add_record(trapeza.Record({k.decode("utf-8"): v.decode("utf-8") for k, v in rec.iteritems()}, inputline = index + 1))

        return source

        
class DelimitedExporter(plugins.Exporter):
    formats = ["csv", "tsv", "chr"]            
    
    def write(self, source, file_like_object, file_format = "csv", sheet_name = None, encoding = "utf-8", line_endings = "\r\n"):
        
        temp_out = io.BytesIO()
        
        writer = csv.DictWriter(temp_out,
                                [header.encode("utf-8") for header in source.headers()],
                                dialect=("excel" if file_format == "csv" else "excel-tab"),
                                lineterminator = line_endings if line_endings in ["\r\n", "\r", "\n"] else "\r\n")
    
        writer.writeheader()
        writer.writerows([{k.encode("utf-8"): v.encode("utf-8") for k, v in record.values.iteritems()} for record in source.records()])
        
        temp_out.seek(0)
        file_like_object.write(temp_out.read().decode("utf-8").encode(encoding))


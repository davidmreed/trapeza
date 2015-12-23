#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  trapeza-match.py
#  
#  Copyright 2013-2014 David Reed <david@ktema.org>
#  This file is available under the terms of the MIT License.
#

# Comparisons
# profile should be a source with the following columns:
# key       master-key      points      strip       compare
#
# Where        key is a key in incoming
#              master-key is the corresponding key in the master source, or blank to use the same key.
#              points is the number of points to assign to a match on this key
#              strip is true if whitespace and quotes ought to be removed from both comparands
#              compare is one of 'exact' (equality);
#                                'prefix' (either value is a prefix of the other);
#                                'fuzzy' (assign a percentage of available points based on similarity).

import argparse
import sys
import pickle
from trapeza.match import *
from trapeza import *


def main():
    parser = argparse.ArgumentParser(description="Manipulate and combine tabular data files. "
                                                 "Use this utility to match incoming records "
                                                 "against an existing data set.")
    parser.add_argument("-o", 
                        "--output", 
                        type=argparse.FileType('wb'), 
                        default=sys.stdout, 
                        help="Specify an output file (default standard output)")
    parser.add_argument("-f", 
                        "--output-format", 
                        choices=formats.available_output_formats(),
                        default="csv",
                        help="Specify an output format. If --output is specified, "
                             "will be inferred from the filename, or defaults to CSV.")
    parser.add_argument("--output-encoding", 
                        default="utf-8",
                        help="For output formats that support Unicode, the desired output encoding. "
                             "UTF-8 is the default.")
    parser.add_argument("-i", 
                        "--input-format", 
                        choices=formats.available_input_formats(),
                        default="csv",
                        help="Treat input read from stdin and from files whose type cannot be inferred as being "
                             "in the specified format. Default is CSV.")
    parser.add_argument("--input-encoding",
                        default="utf-8",
                        help="Treat input data as the specified encoding (for input formats that support Unicode). "
                             "Column names specified on the command line will be treated as the same encoding.")
    parser.add_argument("-p", 
                        "--profile", 
                        type=argparse.FileType('rb'),
                        help="Specify the profile spreadsheet")
    parser.add_argument("-m", 
                        "--master", 
                        type=argparse.FileType('rb'),
                        help="Specify the master spreadsheet")
    parser.add_argument("-M",
                        "--processed-master",
                        type=argparse.FileType('rb'),
                        help="Specify a processed master sheet. The profile information contained within the file will "
                             "be used and any profile specified on the command line will be ignored.")
    parser.add_argument("-n", 
                        "--incoming", 
                        type=argparse.FileType('rb'),
                        help="Specify the incoming spreadsheet")
    parser.add_argument("-c",
                        "--match-cutoff",
                        type=int,
                        default=0,
                        help="The minimum number of points required for a match to appear in the results list.")
    parser.add_argument("--primary-key", 
                        help="Set the column name in the master sheet where unique identifiers are stored.")

    args = parser.parse_args()
    
    if args.incoming is None or args.primary_key is None or \
            ((args.profile is None or args.master is None) and args.processed_master is None):
        sys.stderr.write("{}: you must specify a master, incoming, and profile sheet (or an incoming sheet and "
                         "processed master), and a primary key column.\n".format(sys.argv[0]))
        exit(1)
    
    try:
        incoming = load_source(args.incoming, get_format(args.incoming.name, args.input_format), args.input_encoding)
        if args.processed_master:
            processed_master = pickle.load(args.processed_master)
            profile = processed_master.profile
            master = processed_master.source
        else:
            processed_master = None
            profile = Profile(source=load_source(args.profile, get_format(args.profile.name, args.input_format),
                                                 args.input_encoding))
            master = load_source(args.master, get_format(args.master.name, args.input_format), args.input_encoding)
    except Exception:
        sys.stderr.write("{}: an error occured while loading input files.\n".format(sys.argv[0]))
        return 1
    
    if processed_master is None:
        master.set_primary_key(args.primary_key.decode(args.input_encoding))
    
    results = profile.compare_sources(processed_master or master, incoming, args.match_cutoff)
    output_source = Source(headers=[u"Input Line", u"Unique ID", u"Match Score"])
    
    for result in results:
        output_source.add_record(Record({u"Input Line": str(result.incoming.input_line()),
                                         u"Unique ID": result.master.record_id(),
                                         u"Match Score": str(result.score)}))
        
    try:
        output_format = get_format(args.output.name, args.output_format) 
        write_source(output_source, args.output, output_format, encoding=args.output_encoding)
    except IOError as e:
        sys.stderr.write("{}: an error occured while writing output: {}\n".format(sys.argv[0], e))
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())

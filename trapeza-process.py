#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  trapeza-process.py
#  
#  Copyright 2013-2014 David Reed <david@ktema.org>
#  This file is available under the terms of the MIT License.
#

import argparse
import sys
import cPickle
from trapeza import *
from trapeza.match import *


def main():
    parser = argparse.ArgumentParser(description="Manipulate and combine tabular data files. Use this utility to "
                                                 "process a master data set for use with trapeza-match.")
    parser.add_argument("-o", 
                        "--output", 
                        type=argparse.FileType('wb'), 
                        default=sys.stdout, 
                        help="Specify an output file (default standard output)")
    parser.add_argument("-i", 
                        "--input-format", 
                        choices=formats.available_input_formats(),
                        default="csv",
                        help="Treat input read from stdin and from files whose type cannot be inferred as being in "
                             "the specified format. Default is CSV.")
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
    parser.add_argument("--primary-key", 
                        help="Set the column name in the master sheet where unique identifiers are stored.")

    args = parser.parse_args()
    
    if args.profile is None or args.master is None or args.primary_key is None:
        sys.stderr.write("{}: you must specify a master and profile sheet and a primary key column.\n"
                         .format(sys.argv[0]))
        exit(1)
    try:
        profile = Profile(source=load_source(args.profile, get_format(args.profile.name, args.input_format),
                                             args.input_encoding))
        master = load_source(args.master, get_format(args.master.name, args.input_format), args.input_encoding)
    except Exception:
        sys.stderr.write("{}: an error occured while loading input files.\n".format(sys.argv[0]))
        return 1
    
    master.set_primary_key(args.primary_key.decode(args.input_encoding))

    pm = ProcessedSource(master, True, profile)
    pm.process()

    try:
        cPickle.dump(pm, args.output, protocol=cPickle.HIGHEST_PROTOCOL)
    except Exception as e:
        sys.stderr.write("{}: an error occured while writing output: {}\n".format(sys.argv[0], e))
        return 1
        
    return 0

if __name__ == '__main__':
    exit(main())

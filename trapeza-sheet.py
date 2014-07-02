#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  trapeza.py
#  
#  Copyright 2013-2014 David Reed <david@ktema.org>
#  This file is available under the terms of the MIT License.
#

import argparse, copy, itertools, sys
from trapeza import *

class SortAction(argparse.Action):
    # FIXME: this doesn't work
    def __call__(self, parser, namespace, values, option_string=None):
        if not hasattr(namespace, "sort"):
            setattr(namespace, "sort", [])
        
        if values[0].lower() not in ["string", "number"]:
            raise argparse.ArgumentTypeError("Invalid sort type {} specified.\n".format(values[0]))
                
        getattr(namespace, "sort").append((values[1], True if option_string == "--sort" else False, values[0].lower()))
    
def action_union(sources, keep_duplicates=False):
    first = Source(sources[0].headers(), sources[0].primary_key())

    for source in sources:
        for record in source.records():
            if keep_duplicates or not first.contains_record(record):
                first.add_record(record)
                
    return first
    
def action_intersect(sources):
    first = copy.copy(sources[0])
    
    for source in sources[1:]:
        for record in first.records():
            if not source.contains_record(record):
                first.del_record(record)
                
    return first
    
def action_xor(sources):
    first = Source(sources[0].headers(), sources[0].primary_key())
    removed = Source(sources[0].headers(), sources[0].primary_key())

    for source in sources:
        for record in source.records():
            if first.contains_record(record):
                first.del_record(record)
                removed.add_record(record)
            else:
                if not removed.contains_record(record):
                    first.add_record(record)
    
    return first
    
def action_subtract(sources, keep_duplicates=False):
    first = copy.copy(sources[0])
     
    if not keep_duplicates:
        first = action_union([first], False)
    
    for source in sources[1:]:
        for record in source.reco rds():
            first.del_record(record)
            
    return first

def main():
    parser = argparse.ArgumentParser(description="Manipulate and combine tabular data files.")
    parser.add_argument("--require-consistency", 
                        action="store_true", 
                        default=False,
						help="Require all input sheets to have the same column structure and trigger errors on unexpected values. If not specified, the output file will contain the union of all headers in all sources, and missing values will be filled with blanks.")
    parser.add_argument("-o", 
                        "--output", 
                        type=argparse.FileType('wb'), 
                        default=sys.stdout, 
                        help="Specify an output file (default standard output)")
    parser.add_argument("-f", 
                        "--output-format", 
                        choices = formats.available_output_formats(), 
                        default="csv",
						help="Specify an output format. If --output is specified, will be inferred from the filename, or defaults to CSV.")
    parser.add_argument("--output-encoding", 
                        default="utf-8",
                        help="For output formats that support Unicode, the desired output encoding. UTF-8 is the default.")
    parser.add_argument("-i", 
                        "--input-format", 
                        choices = formats.available_output_formats(),
                        default="csv",
						help="Treat input read from stdin and from files whose type cannot be inferred as being in the specified format. Default is CSV.")
	parser.add_argument("--input-encoding",
                        default="utf-8",
                        help="Treat input data as the specified encoding (for input formats that support Unicode). Column names specified on the command line will be treated as the same encoding.")
    parser.add_argument("--filter", 
                        help="Filter records using the Boolean-valued Python expression provided. Each record is provided as a dictionary called 'record'. If specified together with a combining operation or --add/--drop, filter is run last.")
    parser.add_argument("--sort", 
                        nargs=2,
                        action=SortAction, 
                        metavar=("TYPE", "COLUMN"),
                        help="Sort output rows. The first argument should be 'number' or 'string' and controls the sort type; the second should be the column name. Multiple --sort and --reverse-sort options can be specified to sort on multiple criteria, in order. Sort is run after combination operations and filters.")
    parser.add_argument("--reverse-sort", 
                        nargs=2,
                        action=SortAction, 
                        metavar=("TYPE", "COLUMN"),
                        help="Sort output rows in reverse order. The first argument should be 'number' or 'string' and controls the sort type; the second should be the column name. Multiple --sort and --reverse-sort options can be specified to sort on multiple criteria, in order. Sort is run after combination operations and filters.")
    parser.add_argument("--drop", 
                        metavar="COLUMN",
                        help="Drop columns with the name given. May be specified multiple times. Drop is run after all combining operations.")
    parser.add_argument("--add", 
                        nargs=2, 
                        metavar=("COLUMN", "VALUE"),
                        help="Add a column with the name given and pre-fill the supplied value (which may be the empty string).")

    parser.add_argument("--primary-key", 
                        help="Set the column name where primary record identifiers are stored. If this column is not present in all sources, an error will occur. This option is ignored if --keep-duplicates is specified.")
    parser.add_argument("--keep-duplicates", 
                        action="store_true", 
                        default=False,
                        help="When performing a union or subtract operation, retain duplicate records")
	
    verbs = parser.add_mutually_exclusive_group()
    verbs.add_argument("--union", 
                       action="store_true", 
					   help="Combine all inputs. If --primary-key is provided, use it to identify duplicates; otherwise, use record equality. Earlier rows and earlier sources take precedence (unless --keep-duplicates is specified).")
    verbs.add_argument("--intersect", 
                       action="store_true", 
                       help="Output only rows present in all sources. Identity semantics as in --union. Does not retain duplicates.")
    verbs.add_argument("--subtract", 
                       action="store_true", 
                       help="Subtract, from the first source, any row present in later sources. Identity semantics as in --union. Retains duplicate rows in the first source if --keep-duplicates is specified.")
    verbs.add_argument("--xor", 
                       action="store_true", 
                       help="Output rows present in one and only one source. Identity semantics as in --union. Does not retain duplicates")
	
    parser.add_argument("infile", 
                        nargs="*", 
                        type=argparse.FileType('rb'), 
                        help="An input source.")
    
    args = parser.parse_args()
		
	# Load all sources
    sources = []

    if len(args.infile) < 1:
        sys.stderr.write("{}: no sources were specified.\n".format(sys.argv[0]))
        return 1
        		
    for each_file in args.infile:
        sources.append(load_source(each_file, get_format(each_file.name, args.input_format), args.input_encoding))
        
	# If we are ensuring consistency, quit if the files don't have the same column-set.
	# If not, unify them by adding missing columns.
    if args.require_consistency:
        if not sources_consistent(sources):
            sys.stderr.write("{}: sources are not consistent and --require-consistency was specified.\n".format(sys.argv[0]))
            return 1
    else:
        sources = unify_sources(sources)
        
    # If a primary key was provided, ensure that all records have a primary key.

    if args.primary_key and not args.keep_duplicates:
        for source in sources:
            try:
                source.set_primary_key(args.primary_key.decode(args.input_encoding))
            except Exception as e:
                sys.stderr.write ("{}: one or more records is missing the specified primary key.\n".format(sys.argv[0]))
                return 1
        
    # Determine operation and ensure appropriate inputs are provided
    
    if args.union:
        output = action_union(sources, args.keep_duplicates)
    elif args.intersect:
        output = action_intersect(sources)
    elif args.subtract:
        output = action_subtract(sources, args.keep_duplicates)
    elif args.xor:
        output = action_xor(sources)
    else:
        if len(sources) > 1:
            sys.stderr.write("{}: more than one source was provided, but no combining operator (--union, --intersect, --subtract, --xor) was specified.\n".format(sys.argv[0]))
            return 1
        else:
            # We're operating on a single file.
            output = sources[0]
    
    # Run drop, add, and filter after the combination operations have completed.

    if args.drop:
        output.drop_column(args.drop.decode(args.input_encoding))
    if args.add:
        output.add_column(args.add[0].decode(args.input_encoding), args.add[1].decode(args.input_encoding))
    if args.filter:
        # This is incredibly fucking dangerous and if you run it on a server you're an idiot.
        output.filter_records(lambda rec: bool(eval(args.filter, {"record": rec.values})))
        
    # Sort the final records
    
    if args.sort:
        # FIXME: need Unicode support
        output.sort_records(args.sort)
    
    try:
        output_format = get_format(args.output.name, args.output_format) 
        write_source(output, args.output, output_format, args.output_encoding)
    except Exception as e:
        sys.stderr.write("{}: an error occured while writing output: {}\n".format(sys.argv[0], e))
        return 1
    
	return 0

if __name__ == '__main__':
	exit(main())

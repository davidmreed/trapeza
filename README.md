# Trapeza

Trapeza is a package and set of utility scripts for manipulating 
tabular (i.e., spreadsheet) data. The package is oriented towards 
unformatted record data, such as database dumps, rather than
formatted, typed spreadsheets. Trapeza was originally developed to 
manipulate data output by The Raiser's Edge fundraising software.

Trapeza consists of a package, also called `trapeza`, and the utility 
scripts `trapeza-sheet` and `trapeza-match`. `trapeza-sheet` is 
intended to facilitate the _combining_ in various ways of tabular data 
files. See its usage message for further details. `trapeza-match` 
applies the functionality of the `trapeza.match` module to compare 
"incoming" data, lacking any record identifier, to an existing base of 
data whose records do contain unique identifiers. Again, see the usage 
message for further details.

The package trapeza consists of `trapeza`, which contains the basic
`Source` and `Record` classes as well as load/save and utility code,
and `trapeza.match`, which facilitates detailed comparison between
incoming and existing data to find matches based on a comparison 
profile. File-format support plugins are contained under `formats/` 
but should rarely be of direct interest to the end user.

Trapeza and `trapeza-sheet` can operate on files with and without a
unique primary key. If a primary key is specified, it _must_ be unique
within a given file; if one is not specified, record equality is used
whenever a comparison is required, and duplicate records are permitted
(as modified by a command line argument).

The Trapeza package attempts to support Unicode throughout. Input and
output encodings can be specified on the command line for the utility
scripts (using the names under which Python knows them). UTF-8 is 
the default. CSV and TSV formats are currently supported, and Trapeza
provides a plugin-based format support mechanism.

Unit tests are provided by `test.py`, intended to be run from the 
command line.

Trapeza requires Python 2.7 but has no external dependencies.

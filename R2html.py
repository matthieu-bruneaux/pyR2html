### * Description

# Module to convert an R script to an Rmd text file, which can then be
# processed by knitr to produce an html output

_SCRIPT_DESCRIPTION = (""
"This script will parse a regular R script file into an R markdown\n"
"file, and process it with knitr to produce an html output.\n"
"\n"
"Parsing rules are as follows, and applied in this order:\n"
"- Each lines is stripped of white characters (from the right)\n"
"- The line \"## @end@\" will cause the parser to stop before the end of"
"  the input file\n"
"- If a line ends with \"@\", it is exported as a blank line\n"
"- If a line starts with \"### \", it is considered a header line\n"
"- If a line starts with \"## \", it is considered a code comment (to be\n"
"  exported as a comment in a code chunk in markdown format)\n"
"- If a line starts with \"#\", it is considered a comment (to be exported\n"
"  as normal text in markdown format)\n"
"- All other non-empty lines are considered as code\n"
"\n"
"Header line: The beginning \"### \" are removed, left white characters are\n"
"removed and then the number of stars (\"*\") found at the beginning of the line\n"
"determines the header level (e.g. \"**\" will become \"##\" in markdown). If no\n"
"star is found, an assert statement will fail. The rest of the line (without\n"
"the stars) is then copied after a space to separate the stars from the text.\n"
"\n"
"R code comment line: The first \"#\" is removed (leaving \"# \") and the line is\n"
"embedded in a code chunk as for regular R code (see \"code line\" below)\n"
"\n"
"Comment line: All left \"#\" and \" \" are removed, and the line is then copied\n"
"as is in the markdown output.\n"
"\n"
"Code line: Each code line is embedded between \"```{r}\\n\" and \"\\n```\". When\n"
"all the input text has been processed, \"```\\n```{r}\\n\" strings are removed\n"
"from the output so that adjacent lines of code are in the same code chunk.\n")
                      
### ** Usage

# python script.py myRscript [arguments passed to the R script]


### * Setup

### ** Import

import sys
import subprocess
import os
import shutil
import random
import argparse

### ** Parameters

_MY_TAG_LENGTH=6

# myInputFile = sys.argv[1]
# myArgumentsToRScript = sys.argv[2: ]
# cleanupRmdFile = True
# cleanupMdFile = True
# logging.info("Input file is: " + myInputFile)
# if myInputFile.endswith(".R") :
#     myRawFile = myInputFile[:-2]
# else :
#     myRawFile = myInputFile
# myOutputFileRmd = myRawFile + ".Rmd"
# logging.info("Rmd output file is: " + myOutputFileRmd)

### *** Extra CSS

INSERT_AFTER_PATTERN= """

   h2, h3 {
      page-break-after: avoid;
   }
}
</style>
"""

# Other colors for headings:
# lightblue
# orange
# lightgreen
# indianred
# orchid

EXTRA_CSS = """

<!-- Floating TOC, cf. http://rpubs.com/stevepowell99/floating-css -->
<style type="text/css">
#toc {
  position: fixed;
  left: 0;
  top: 0;
  width: 300px;
  height: 100%;
  overflow:auto;
  padding-left: 10px;
  padding-top: 5px;
  background: #111111;
  color: #888888;
}

#toc-header {
  text-align: center;
}

#toc a {
  color: #888888;
  text-decoration: none;
}

#toc ul {
  color: #888888;
  margin-left: 0px;
  padding-left: 7px;
  list-style-type: disc;
}

#toc ul a {
  text-decoration: underline;
  color: #BAE4BC;
}

#toc ul ul a {
  text-decoration: none;
  color: #7BCCC4;
}

#toc ul ul ul a {
  color: #43A2CA;
}

#toc ul ul ul ul a {
  color: #0868AC;
}

#toc ul ul ul ul ul a {
  color: #F0F9E8;
}

body {
	margin-left: 310px;
}

table {
  margin: auto;
    border-collapse: collapse;
}

th,td {
  padding-left: 10px;
  padding-right: 10px;
  text-align: center;
}

thead {
 
  border-bottom: 1pt solid black;
}


</style>

"""

### * Functions

### ** randomTag(n)

def randomTag(n) :
    """Generate a random tag of size n.

    Args:
        n (int): Length of the tag

    Returns:
        str: A tag of length n, which each character in [0-9][a-f]
    """
    o = ""
    allowed = "0123456789abcdef"
    for x in range(n) :
        o += random.choice(allowed)
    return o

### ** _parseHeader(line)

def _parseHeader(line) :
    """Parse a header line (starting with "###"). The level of the header 
    depends on the number of "*" after the initial "###".
    
    Args:
        line (str): A string which must start with "### "

    Returns:
        str: The input string suitably modified to be a markdown header
    """
    assert line.startswith("### ")
    line = line[4: ].lstrip()
    n_stars = 0
    while line[0] == "*" :
        line = line[1: ]
        n_stars += 1
    assert n_stars > 0
    return("#" * (n_stars + 1) + " " + line)

### ** _parseRcodeComment(line)

def _parseRcodeComment(line) :
    """Parse an R code comment line by removing one comment character and 
    embedding the comment in a code chunk.

    Args:
        line (str): A string starting with "## "

    Returns:
        str: The input line with one left "#" removed and embedded in a code 
          chunk
    """
    assert line.startswith("## ")
    line = line[1: ]
    return("```{r}\n" + line + "\n```")

### ** _parseComment(line)

def _parseComment(line) :
    """Parse a comment line by removing the comment character(s).

    Args:
        line (str): A string starting with "#"

    Returns:
        str: The input line with all left trailing "#" removed
    """
    assert line[0] == "#"
    return(line.lstrip("# "))

### ** _parseCode(line)

def _parseCode(line) :
    """Parse a code line. For now just put backticks before and after each code
    line, which is not very elegant.

    Args:
        line (str): A code string

    Returns:
        str: The input line formatted as R code for R markdown
    """
    return("```{r}\n" + line + "\n```")

### ** _insertInFile(filename, pattern, insert)

def _insertInFile(filename, pattern, insert) :
    """Insert a string into a file content

    Args:
        filename (str): Input file (will be overwritten)
        pattern (str): String is inserted after the first occurrence of this
          pattern
        insert (str): String to insert

    Returns:
        None, but overwrites the input file. If pattern is not found, the 
          content is not modified
    """
    with open(filename, "r") as fi:
        content = fi.read()
    location = content.find(pattern)
    if (location < 0):
        pass
    else:
        location = location + len(pattern)
        content = content[0:location] + insert + content[location:]
        with open(filename, "w") as fo:
            fo.write(content)
    return None
    
### ** parseInputFile(filename)

def parseInputFile(filename) :
    """Parse the content of an R input file.

    Args:
        filename (str): Path to the input file

    Returns:
        str: A string containing the parsed content, ready to be written in an 
          output file.
    """
    r = ""
    with open(filename, "r") as fi :
        for l in fi :
            # We read line by line
            l = l.rstrip()
            if l == "## @end@" :
                print("End tag detected, skipping the rest of the file")
                for l in fi :
                    pass
                l = ""
            elif l.endswith("@") :
                l = ""
            elif l.startswith("### ") :
                l = _parseHeader(l)
            elif l.startswith("## ") :
                l = _parseRcodeComment(l)
            elif l.startswith("#") :
                l = _parseComment(l)
            elif len(l) > 0 :
                l = _parseCode(l)
            else :
                pass
            r += l + "\n"
    # Join adjacent R code chunks
    r = r.replace("```\n```{r}\n", "")
    return(r)

### ** knitRmdFile(RmdFile, argumentsToRscript)

def knitRmdFile(RmdFile, argumentsToRScript) :
    """Use the knitr package in R to generate an html output from an Rmd file.

    Args:
        RmdFile (str): Path to the Rmd file
        argumentsToRScript (list): Arguments to be passed to the R (Rmd) script

    Returns:
        Nothing, but an html file is produced (and also the intermediate md file)
    """
    figureFolder = "figure." + randomTag(_MY_TAG_LENGTH)
    assert not os.path.isdir(figureFolder)
    c = ["Rscript"]
    c.append("-e")
    Rcmd = "library(knitr); "
    #Rcmd += "options(markdown.HTML.stylesheet = \"main.css\"); "
    # http://stackoverflow.com/questions/28295282/controlling-the-output-from-knit2html
    Rcmd += "opts_chunk$set(fig.path=\"" + figureFolder + "/\"); "
    Rcmd += "opts_chunk$set(fig.width=11); "
    Rcmd += "opts_chunk$set(dev=\"CairoPNG\"); " # https://gist.github.com/taniki/5133358
    Rcmd += "knit2html(\"" + RmdFile + "\", options = c(\"toc\", markdown::markdownHTMLOptions(TRUE)))"
    c.append(Rcmd)
    if not type(argumentsToRScript) is list :
        argumentsToRScript = list(argumentsToRScript)
    c += argumentsToRScript
    p = subprocess.Popen(c)
    retValue = p.wait()
    shutil.rmtree(figureFolder)
    return(retValue)

### * Main script functions

### ** _makeParser()

def _makeParser() :
    """Build the argument parser for the main script.
    
    Returns:
        argparse.ArgumentParser() object: An argument parser object ready to be
        used to parse the command line arguments
    """
    parser = argparse.ArgumentParser(
        description = _SCRIPT_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    # R script
    parser.add_argument("rscript", nargs = 1, type = str,
                        metavar = "R_SCRIPT",
                        help = "R script filename")
    # arguments for the R script
    parser.add_argument("arguments", metavar = "R_ARGUMENTS", type = str,
                        nargs = "*", default = [],
                        help = "Arguments passed to the R script")
    # --keepRmd
    parser.add_argument("--keepRmd", action = "store_true",
                        help = "Keep the Rmd file after html generation")
    # --keepMd
    parser.add_argument("--keepMd", action = "store_true",
                        help = "Keep the Md file after html generation")
    return parser
    
### ** _main()

def _main() :
    """Main function, used by the command line script. This function contains 
    the basic logic of the script.

    """

    # Arguments
    parser = _makeParser()
    args = parser.parse_args()

    # Parse the R script into Rmd
    rmdFile = args.rscript[0] + "." + randomTag(_MY_TAG_LENGTH) + ".Rmd"
    with open(rmdFile, "w") as fo :
        fo.write(parseInputFile(args.rscript[0]))

    # Convert the Rmd file to html output
    knitRmdFile(rmdFile, args.arguments)
    # Add extra CSS
    _insertInFile(rmdFile[:-4] + ".html", INSERT_AFTER_PATTERN, EXTRA_CSS)
    
    # Cleanup
    if not args.keepRmd :
        os.remove(rmdFile)
    if not args.keepMd :
        os.remove(rmdFile[:-4] + ".md")

    # Change the html output name
    os.rename(rmdFile[:-4] + ".html", args.rscript[0][:-2] + ".html")

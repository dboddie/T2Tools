# CMDSyntax - a library for parsing command line arguments according to a
# syntax definition.
# 
# Copyright (c) 2002, David Boddie
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
# 
# 
# Note:
# 
# The TkForm class is inspired and based on Fredrik Lundh's ScrolledFrame
# example widget:
#
# http://mail.python.org/pipermail/python-list/1999-October/013255.html

"""
cmdsyntax.py

A library for parsing command line arguments according to a syntax
definition, returning dictionaries of values where the command line
complies with the required syntax.

The syntax string is made up of labels, switches, commands, brackets and
operators. Combinations of these items allow the syntax definition to
specify a variety of command lines in a familiar format. In addition, the
syntax definition can be presented in an understandable form to the user.

Additionally, the style of the syntax used can be customized for the
convenience of the developer. The style of the arguments passed from the
command line can also be specified to support platform-specific
conventions for command line utilities.


Quick example:

import sys, cmdsyntax, pprint

s = cmdsyntax.Syntax("[-v] infile [-o outfile]")

match = s.get_args(sys.argv[1:])

pprint.pprint(match)


The items which make up the syntax definition are as follows.


Labels (alphanumeric characters)

Arguments made up entirely of alphanumeric characters represent arbitrary
values on the command line. The corresponding command line values are
stored under the labels defined in the syntax definition.


Switches (- or -- followed by a label)

Switches may be specified as either beginning with a single dash or a
double dash. This may be changed by customizing the style used to
describe the syntax definition.

Switches which contain a single dash followed by a label of only one
alphanumeric character must be matched exactly by the corresponding
argument on the command line.

e.g. -a

Those that begin with a single dash and more than one alphanumeric
character represent a set of possible single character label switches
which can be used in any order. At least one of these switches must be
found at the corresponding position on the command line.

e.g. -abcde corresponds to at least one of -a -b -c -d -e

Those that begin with a double dash may take two forms: the first is the
equivalent to the single dash, single character label switch; the second
contains an equals sign, allowing the switch to be assigned a value.

e.g. --output-dir=dir assigns the value found to --output-dir


Commands (a string enclosed in double quotes)

To specify commands that must be supplied by the user, we use strings
enclosed in double quotes. These behave like switches in their simplest
form, but are less restrictive in the range of characters which may be
used.

For example,

    "add"|"remove" file

will require that the user explicitly writes either "add" or "remove"
before the file that they specify. The user need not specify the command
in quotes.


Extended labels (a string enclosed in a < > pair)

To allow more verbose labels, the syntax definition can contain strings
enclosed in angled brackets. Such items are treated exactly like ordinary
labels but allow a greater range of characters.

For example,

    <your input file> <my output file>

will produce entries in the match dictionary called "your input file" and
"my output file".


The sequence (AND) operator [space]

Arguments which are separated by a space must both be supplied from the
command line in the order given. So the syntax definition

    infile outfile

requires that two arguments be supplied from the command line. The first
will be stored under the name "infile" and the second under the name
"outfile".


The exclusive OR operator |

This is used to select one of a list of items, usually switches.

For example,

    -a|-b|-c

allows only one of -a -b -c    


Grouping of arguments using brackets

Arguments may be grouped together to avoid ambiguity by using either
ordinary or square brackets.

Grouping (arguments enclosed within a ( ) pair)

This is useful when using the EOR operator to select between a series of
multiple argument options.

e.g. (-i infile)|(-o outfile)


Optional arguments (arguments enclosed within a [ ] pair)

To indicate that arguments are optional, they must be enclosed within
square brackets.

e.g. infile [-o outfile] causes only one argument to be required


Selections of arguments (arguments enclosed within a { } pair)

Selections are used to require that one or more of a group of arguments
are specified on the command line.

e.g. {--send-e-mail --send-postcard --telephone-call}

will require the user to specify at least one of the options given.

"""

__author__  = "David Boddie <david@boddie.net>"
__date__    = "2 May 2002"
__version__ = "0.52"

import copy, string, types


class cmdsyntax_error(Exception):

    pass


class matching_error(Exception):

    pass


# Class containing useful common methods.

class Abstract:

    def read_string(self, s, allow = None, end = None):
        """new = read_string(self, s, allow = None, end = None)
        
        Read the string passed from the start up to any characters contained
        in a list of forbidden characters and return the result.
        
        s is the string to be read.
        allow is a string of allowed characters.
        end is a string of delimiting characters.
        
        If allow is set then only those characters are allowed, and any
        other characters are considered to be delimiters.
        If end is set, and allow is not set then all characters except
        those in the delimiting string are read.
        """
    
        new = ''
    
        if allow != None:
        
            for char in s:
            
                if char in allow:
                
                    new = new + char
                
                else:
                
                    break
    
        elif end != None:
        
            ended = 0
            
            for char in s:
        
                if char not in end:
        
                    new = new + char
        
                else:
                
                    # Ended satisfactorily.
                    ended = 1
        
                    break
        
            if ended == 0:
            
                # We reached the end of the text without encountering an
                # end character.
                
                raise cmdsyntax_error, \
                      "End of string reached, where one of {" + end + \
                      "} was expected."
                
        else:
        
            raise cmdsyntax_error, "Cannot read string %s with no explicitly" + \
                                   " allowed characters and no explicitly" + \
                                   " forbidden characters."
        
        return new
    
    
class Style(Abstract):
    """style_object = Style()
    
    Create a style object with standard definitions of the characters used
    to denote grouping of elements and particular types of objects commonly
    found on command lines.
    """
    
    # Characters with special meaning for the syntax parser, denoting the
    # grouping of elements and the type of elements found.
    
    # To be defined by the user:
    collect_start  = '('
    collect_end    = ')'
    optional_start = '['
    optional_end   = ']'
    select_start   = '{'
    select_end     = '}'
    ext_start      = '<'
    ext_end        = '>'
    string_start   = '"'
    string_end     = '"'
    and_operator   = ' '
    eor_operator   = '|'
    
    labels         = string.letters + string.digits
    in_labels      = labels
    
    in_string   = string.letters + string.digits
    switches    = '-'
    in_switch   = switches + in_string + '='
    
    # Types of switch, command and other objects to expect.
    
    # Allow types of switch/option:
    
    allow_double       = 1   # e.g. --option
    allow_double_value = 1   # e.g. --option=value
    allow_single_value = 0   # e.g. -o=value
    allow_single_long  = 0   # e.g. -name
    expand_single      = 1   # e.g. -abc -> -a -b -c
    
    # Automatically constructed strings:
    collections = collect_start + collect_end + optional_start + \
                  optional_end + select_start + select_end
    
    operators   = and_operator + eor_operator
    strings     = string_start + string_end + ext_start + ext_end
    special     = strings + collections + switches + operators
    
    # Characters with which to recognise certain types of element.
    
    def __init__(self):
    
        pass
    
    def verify(self):
        """success = verify(self)
        
        Builds the automatically constructed strings
        Check for contradictions in this style.
        Returns 1 if this style is consistent, 0 otherwise.
        """
        
        if self.and_operator == self.eor_operator:
        
            return 0
        
        elif self.and_operator in string.whitespace and \
             self.eor_operator in string.whitespace:
        
            return 0
        
        # Build strings:
        self.collections = self.collect_start + self.collect_end + \
                           self.optional_start + self.optional_end + \
                           self.select_start + self.select_end
        
        self.operators   = self.and_operator + self.eor_operator
        self.special     = self.strings + self.collections + self.switches + \
                           self.operators
        
        # Option styles:
        if self.allow_single_long == 1 and self.expand_single == 1:
        
            return 0
        
        # Success
        return 1
    
    def is_option(self, text):
        """answer = is_option(self, text)
        
        Determines whether the text represents an option in this style.
        """
        
        if text[0] in self.switches:
        
            return 1
        
        else:
        
            return 0
        
    def unstyle_option(self, text, for_definition):
        """option = unstyle_option(self, text, for_definition)
        
        Create a canonical option object by removing the style information
        from the text given for a switch.
        
        If for_definition is not equal to zero then key value options
        must include a name for the value or an exception is raised.
        
        If for_definition is equals to zero then a trailing = can be
        accepted in key value options from the command line to indicate
        that an empty value was given.
        """
        
        # Check the form of the switch for errors.
        leading = self.read_string(text, self.switches)
        
        if len(leading) == 1:
        
            # Single switch
            if string.count(text, '=') > 0:
            
                if self.allow_single_value == 0:
                
                    # Key value form not allowed.
                    raise cmdsyntax_error, \
                          "Forbidden form of switch (%sx=value): %s" % \
                          (text[0], text)
                else:
                
                    # Key value form allowed.
                    if string.find(text, '=') > 2 and \
                       self.allow_single_long == 0:
                    
                        # More than one letter found.
                        raise cmdsyntax_error, \
                              "Forbidden form of switch (%sname=value): %s" % \
                              (text[0], text)
            else:
            
                # Check for multiple characters.
                if len(text) > 2 and self.expand_single == 0 and \
                   self.allow_single_long == 0:
                
                    raise cmdsyntax_error, \
                          "Forbidden form of switch (%sabc): %s" % \
                          (text[0], text)
        
        elif len(leading) == 2:
        
            # Double switch
        
            if self.allow_double == 0:
            
                raise cmdsyntax_error, \
                      "Forbidden form of switch (%sname): %s" % \
                      (text[0:1], text)
            
            if string.count(text, '=') > 0 and \
               self.allow_double_value == 0:
                
                    # Key value form not allowed.
                    raise cmdsyntax_error, \
                          "Forbidden form of switch (%sname=value: %s" % \
                          (text[0:1], text)
            #else:
            #
            #    # The form of the switch was not recognised.
            #    raise cmdsyntax_error, \
            #          "Unexpected form of switch: %s" % text
        
        # If we are not allowed to have key value switches
        # then an exception has been raised. Therefore we
        # can examine the switches for problems which will
        # only occur with key value switches without
        # causing problems if they are not allowed.
        
        if string.count(text, '=') > 1:
        
            raise cmdsyntax_error, \
                  "Too many equals signs in switch: %s" % text
        
        elif text[-1] == '=' and for_definition == 1:
        
            raise cmdsyntax_error, \
                  "Trailing equals sign in switch: %s" % text
        
        elif string.find(text[len(leading):], '=') == 0:
        
            # The first character was an equals sign.
            raise cmdsyntax_error, \
                  "Leading equals sign in switch: %s" % text
        
        # Add an Option object to this node.
        name = text[len(leading):]
        
        if string.count(text, '=') > 0:
        
            # Key value option: extract the name and value from the text.
            name = name[:string.find(name, '=')]
            value = text[string.find(text, '=') + 1:]
        
        else:
            value = None
        
        # If this is a single switch which is to be expanded into
        # multiple options then return a Selection object.
        if len(leading) == 1 and len(name) > 1 and value == None and \
           self.expand_single == 1:
        
            names = []
            
            for char in name:
            
                names.append( Option(char) )
            
            return Selection( names, 1 )
        
        else:
        
            # Return an Option object.
            return Option(name, value)

class Selection:
    """selection = Selection(list, minimum, maximum = len(list))
    
    Create an object which represents a list of objects of which a
    particular number need to be selected.
    """
    
    def __init__(self, l, mini, maxi = None):
    
        self.objects = l
        self.minimum = mini
        
        if maxi != None:
            self.maximum = maxi
        else:
            self.maximum = len(l)
        
        if self.maximum < self.minimum:
        
            raise cmdsyntax_error, \
                  "Selections must require a maximum number of objects " + \
                  "to be chosen which is greater than the minimum."
        
        if maxi == 0:
        
            raise cmdsyntax_error, \
                  "Selections requiring a maximum of zero objects to be " + \
                  "chosen are not allowed."
        
        # An attribute for whether the permutations can be read.
        self.setup = 0
        
    def __repr__(self):
    
        return "Selection of %i to %i from %s" % \
               (self.minimum, self.maximum, repr(self.objects))
    
    def selection(self):
        """list = selection(self)
        
        Using the selected attribute, return a permutation of the selection
        as a list of objects to be matched.
        """
        
        # Only return permutations if the begin method has been called.
        if self.setup == 0:
        
            raise cmdsyntax_error, "Permutations of objects in a Selection " + \
                  "object must be set up by calling the begin method."
        
        items = []
        available = copy.copy(self.objects)
        
        for index in self.selected:
        
            # The items are removed from the list of available objects.
            items.append( available[index] )
            
            del available[index]
        
        return items
    
    def begin(self):
        """list = begin(self)
        
        Return the first permutation of the objects in the selection.
        """
        
        # Enable permutations to be read.
        self.setup = 1
        
        # Create a list containing the indices of the selected objects.
        # This will be used by the next and prev methods to determine
        # the next and previous permutations.
        
        # There must be at least one object selected, but no less than the
        # minimum number.
        self.selected = []
        
        for i in range(0, max(1, self.minimum)):
        
            self.selected.append(0)
        
        # Increment the last index in the selected list.
        self.inc_index = len(self.selected) - 1
        
        return self.selection()
    
    def next(self, method = "width"):
        """list = next(self, method = "width")
        
        Return the next permutation of all the objects in the selection
        or None if there are no more permutations.
        
        The method parameter specified whether the next permutation will be
        found by searching the tree by width
        
        e.g. with indices [0] -> [1] -> [2] -> [0, 0]
        
        or by depth
        
        e.g. with indices [1] -> [1, 0] -> [1, 0, 0]
        """
        
        #print self.selected
        # Only return permutations if the begin method has been called.
        if self.setup == 0:
        
            raise cmdsyntax_error, "Permutations of objects in a Selection " + \
                  "object must be set up by calling the begin method."
        
        if method == "width":
            return self.next_width()
        
        else:
            return self.next_depth()
    
    def next_width(self):
    
        while 1:
        
            if len(self.selected) > self.maximum:
            
                # Prevent further reading of permutations.
                self.setup = 0
                return None
            
            # Increment the last index in the selected list.
            self.selected[self.inc_index] = self.selected[self.inc_index] + 1
            
            # The allowed index depends on its position in the list.
            # For a selection which allows all objects to be included,
            # the last index will always be zero, indicating that it
            # refers to the last available object.
            #
            # e.g. For two objects, "a" and "b", we can have indices of
            #      [0, 0] and [1, 0] referring to
            #      ["a", "b"] and ["b", "a"]
            
            if self.selected[self.inc_index] >= \
               len(self.objects)-self.inc_index:
                
                # The last index is outside the permitted range.
                
                # Zero all the indices from the current one onwards.
                for i in range(self.inc_index, len(self.selected)):
                
                    self.selected[i] = 0
                
                if self.inc_index > 0:
                
                    # Next time, increment the previous index instead.
                    self.inc_index = self.inc_index - 1
                
                else:
                
                    # There isn't a previous index, so try to add
                    # an extra index to the end of the list of indices.
                    if len(self.selected) < self.maximum:
                    
                        self.selected.append(0)
                        
                        # The index to be incremented is the last in the
                        # list again.
                        self.inc_index = len(self.selected) - 1
                        
                        # Return this new selection.
                        return self.selection()
                    
                    else:
                    
                        # No more indices can be added.
                        # Prevent further reading of permutations.
                        self.setup = 0
                        return None
                
            else:
            
                # The index was incremented successfully.
                
                # If this isn't the last index in the list then ensure
                # that the next increment occurs in the next index.
                
                if self.inc_index < len(self.selected) - 1:
                
                    self.inc_index = self.inc_index + 1
                
                # Return the selection.
                return self.selection()
    
    def next_depth(self):
    
        # Try to add indices to the list.
        
        if len(self.selected) < self.maximum:
        
            # The allowed index depends on its position in the list.
            # For a selection which allows all objects to be included,
            # the last index will always be zero, indicating that it
            # refers to the last available object.
            #
            # e.g. For two objects, "a" and "b", we can have indices of
            #      [0, 0] and [1, 0] referring to
            #      ["a", "b"] and ["b", "a"]
            
            # Add another index to the list of indices.
            self.selected.append(0)
            self.inc_index = len(self.selected) - 1
            
            # Return this selection using the indices.
            return self.selection()
        
        else:
        
            # We cannot select any more objects, so we must either increment
            # the index at this level or ascend the list to find an entry
            # which we can safely increment.
            
            while self.inc_index >= 0:
            
                # If we can, remove the last index in the list.
                
                if self.inc_index == 0:
                
                    # We can't ascend any further.
                    # Give up.
                    break
                
                elif self.inc_index >= self.minimum:
                
                    # There are more than the minimum number of indices
                    # required so we can remove the last index in the
                    # list of indices.
                    self.selected.pop()
                    self.inc_index = self.inc_index - 1
                
                else:
                
                    # We need at least the minimum number of indices
                    # to be present in the list, so increment a previous
                    # index, but do not remove any indices.
                    
                    # Zero all the indices from the current one onwards.
                    for i in range(self.inc_index, len(self.selected)):
                    
                        self.selected[i] = 0
                    
                    self.inc_index = self.inc_index - 1
                
                # Increment the relevant index in the list.
                self.selected[self.inc_index] = \
                    self.selected[self.inc_index] + 1
                
                if self.selected[self.inc_index] >= \
                    len(self.objects)-self.inc_index:
                
                    # The index is too high for the number of objects
                    # remaining this deep in the selection.
                    
                    # We must loop again and find an earlier index to
                    # increment.
                    pass
                            
                else:
                
                    # The next time we increment an index, it will be the
                    # one at the end of the list.
                    self.inc_index = len(self.selected) - 1
                    
                    # Select objects using these indices.
                    return self.selection()
            
            # No more permutations are available.
            # Prevent further reading of permutations.
            self.setup = 0
            return None


class Option:
    """option = Option(name, value = None)
    
    Define an option object corresponding to the use of a switch on the
    command line with the given name and with a possible value assignment.
    """
    
    def __init__(self, name, value = None):
    
        self.name = name
        self.value = value
    
    def __repr__(self):
    
        if self.value != None:
        
            return "Option: %s = %s" % (self.name, self.value)
        
        else:
        
            return "Option: %s" % self.name

class Command:
    """command = Command(name)
    
    Define a string which must be matched exactly on the command line.
    """
    
    def __init__(self, name):
    
        self.name = name
    
    def __repr__(self):
    
        return "Command: %s" % self.name

class Syntax(Abstract):
    """syntax_object = Syntax(syntax_definition, syntax_style = None)
    
    Create a syntax object to describe the syntax definition passed as a
    string with a given style described by an instance of the Style
    class.
    
    The style definition
    """

    def __init__(self, syntax, style = None):
            
        # Record the syntax definition.
        self.syntax = syntax
        
        # Create an instance of the default style if necessary.
        if style == None:
        
            style = Style()
        
        # Produce a tree from the syntax definition.
        self.syntax_tree, pos = self.parse_syntax(syntax, style)
            
        if pos < len(syntax):
            
            raise cmdsyntax_error, "Not all the syntax definition was read."+\
                  " Remaining text: " + syntax[pos:]


    def get_args(self, args, find_first = 1, in_order = 0, style = None):
        """dict = get_args( self, args, find_first = 1, in_order = 0,
                            style = None)

        Return a dictionary containing the labels corresponding to each
        argument specified for this syntax object. This method quickly
        matches the command line arguments against the syntax definition
        and may fail to match against syntaxes which are ambiguous or
        contain repeated elements.
    
        args is either a list of arguments from the command line, usually
        supplied by sys.argv, or a raw string containing arguments.
        
        find_first = 1 causes the first match to be returned;
        find_first = 0 returns all possible matches.
        
        The order of optional arguments is not important by default, but
        if in_order is non-zero then optional arguments must be specified
        on the command line in the order given in the syntax definition.
        
        The style of command line, if omitted, assumes the default form.
        """
        
        # If the command line arguments were passed as a string then convert
        # them to a list.
        if type(args) == types.StringType:
        
            args = self.create_argv(args)
        
        # If no style was required then create an instance of the default
        # style.
        
        if style == None:
        
            style = Style()
        
        # Expand any single dash switches with multiple characters.
        if style.expand_single == 1:
        
            args = self.expand_args(args, style)
        
        # Attempt to fit the command line input to one of the permutations
        # possible in the syntax tree.
        
        matches, argslist = self.match_arguments(
                                self.syntax_tree, args, in_order,
                                style, find_first )
        
        # Examine all the matches and remove any which have command line
        # arguments left over as this indicates a failure to match them
        # with the syntax definition.
        new_matches = []
        
        for m in range(len(matches)):
        
            if argslist[m] == len(args):
            
                new_matches.append(matches[m])
        
        return new_matches


    def parse_syntax(self, syntax, style, pos = 0, end = None):
        """syntax_tree, pos = parse_syntax(self, syntax, style, pos, end)
        
        Recursively parse the syntax definition with a given style and
        return a tree of elements.
        
        syntax is the syntax definition for the program's invocation.
        pos is the offset into the syntax definition.
        end is the type of nested bracket expected to end parsing at this level.
        """
        
        # Skip whitespace. (This isn't really necessary as spaces
        # will be ignored while labels are being looked for.)
        text = self.read_string(syntax[pos:], string.whitespace)
                    
        pos = pos + len(text)

        # Create an empty list and a placeholder node.
        tree = []
        node = []
    
        # Expect a sequence of labels or switches separated by operators.
        next = "label"
    
        # Examine the syntax string from the current offset and act
        # accordingly.
        while pos < len(syntax):
        
            char = syntax[pos]
            
            if char == style.ext_end:
            
                # Unexpected end of an extended label.
                
                raise cmdsyntax_error, \
                      "Unexpected "+char+" found in syntax definition at" + \
                      "offset %i: %s" % (pos, syntax[pos:])
            
            elif char == style.optional_end or \
                 char == style.collect_end or \
                 char == style.select_end:
                
                # End of optional or grouped argument list.
                
                # If another type of argument list is being read then this
                # character is unexpected.
                
                if end != char:
                
                    raise cmdsyntax_error, \
                          "Unexpected "+char+" found, where "+str(end) + \
                          " was expected in syntax definition at offset" + \
                          " %i: %s" % (pos, syntax[pos:])
                
                # If an operator was expected then we have just read a
                # value and may return the items in the sequence to the
                # level above.
                
                if next == "operator":
                
                    # Return the tree of nodes to the level above, ensuring
                    # that any optimisation has already been performed.
                    
                    tree = tree + self.optimise(node)
                    
                    # Allow for unordered optional items by converting
                    # groups of optional items into a Selection object
                    # which chooses between zero and the total number
                    # of grouped items.
                    tree = self.group_options(tree)
                    
                    # Return the tree list.
                    return tree, pos + 1
                
                elif next == "label":
                
                    # A label was expected. This character was either
                    # preceded by an AND operator or an EOR operator.
                    
                    if node == []:
                    
                        # An empty node indicates that we encountered
                        # whitespace which was mistaken for an operator.
                        
                        # Allow for unordered optional items by converting
                        # groups of optional items into a Selection object
                        # which chooses between zero and the total number
                        # of grouped items.
                        tree = self.group_options(tree)
                        
                        # Return the tree to the level above.
                        return tree, pos + 1
                    
                    else:
                    
                        # A non-empty node indicates that we encountered
                        # an EOR operator immediately before this character.
                        
                        # This is invalid use of the operator in the syntax
                        # definition.
                        
                        raise cmdsyntax_error, \
                              "Expected a label, but instead found "+char + \
                              " at offset %i: %s" % (pos, syntax[pos:])
            
            # If a label is expected then read it.
            elif next == "label":
            
                if char in string.whitespace:
                
                    # In the context of looking for a label, whitespace
                    # is ignored.
                    pos = pos + 1
                
                    # The next item in the sequence should be a label.
                    next = "label"
                
                elif char not in style.special:
    
                    # Read the string found here and store the result in this
                    # node's list of strings.
        
                    text = self.read_string(syntax[pos:], style.in_string)
                                                                # delimiters were
                                                                # "self.special"
        
                    node.append( text )
        
                    # Update the syntax definition offset.
                    pos = pos + len(text)
                
                    # The next item in the sequence should be an operator.
                    next = "operator"
                
                elif char == style.string_start:
    
                    # A command string: read all the characters inside up to
                    # another quotation mark and store the result in a child
                    # node of the current placeholder node.
        
                    text = self.read_string( syntax[pos+1:],
                                             style.in_string,
                                             style.string_end )
                    
                    # Add a Command object to this node.
                    node.append( Command(text) )
        
                    # Update the syntax definition offset.
                    pos = pos + len(text) + 2
                
                    # The next item in the sequence should be an operator.
                    next = "operator"
                
                elif char in style.switches:
            
                    # A switch: read the characters following it as a string
                    # and store the result in the current placeholder node.
                    
                    text = self.read_string(syntax[pos:], style.in_switch)
                    
                    node.append( style.unstyle_option(text, 1) )
                    
                    # Update the syntax definition offset.
                    pos = pos + len(text)
                
                    # The next item in the sequence should be an operator.
                    next = "operator"
                
                elif char == style.optional_start:
                
                    # Optional arguments.
                    
                    # Create an empty child node and continue parsing from there,
                    # updating the syntax definition offset.
                    
                    lower_tree, pos = self.parse_syntax(
                                          syntax, style, pos+1,
                                          end = style.optional_end )
                    
                    # If there is an optional list of arguments encoded in a
                    # child node then there must be an empty node available
                    # as an alternative.
                    # If there is nothing in the level below then don't
                    # bother to place any nodes there.
                    
                    if lower_tree != []:
                    
                        # Add nodes and an alternative empty node to the level
                        # below.
                        node.append( lower_tree )
                        node.append( [] )
                
                    # The next item in the sequence should be an operator.
                    next = "operator"
                
                elif char == style.collect_start:
                
                    # Grouped arguments.
                    
                    # Create an empty child node and continue parsing from there,
                    # updating the syntax definition offset.
                    
                    lower_tree, pos = self.parse_syntax(
                                          syntax, style, pos+1,
                                          style.collect_end )
                    
                    if lower_tree != []:
                    
                        # Add nodes to the level below.
                        node.append( lower_tree )
                    
                    # The next item in the sequence should be an operator.
                    next = "operator"
                
                elif char == style.select_start:
                
                    # Selection of arguments.
                    
                    # Create an empty child node and continue parsing from
                    # there, updating the syntax definition offset.
                    
                    lower_tree, pos = self.parse_syntax(
                                          syntax, style, pos+1,
                                          style.select_end )
                    
                    if lower_tree != []:
                    
                        # Add nodes to the level below.
                        node.append( Selection(lower_tree, 1) )
                    
                    # The next item in the sequence should be an operator.
                    next = "operator"
                
                elif char == style.ext_start:
                
                    # Mandatory named argument.
                    
                    # Behaves as a string: read all the characters inside up to
                    # a > and store the result in a child node of the
                    # current placeholder node.
                    
                    text = self.read_string( syntax[pos+1:], None,
                                             style.ext_end )
                    
                    node.append( text )
                    
                    # Update the syntax definition offset.
                    pos = pos + len(text) + 2
                
                    # The next item in the sequence should be an operator.
                    next = "operator"
                
                else:
                
                    # We expected a label, but found something else
                    # instead.
                    
                    raise cmdsyntax_error, \
                          "Expected a label, but instead found "+repr(char) + \
                          " at offset %i: %s" % (pos, syntax[pos:])
            
            # If an operator is expected then read it.
            elif next == "operator":
            
                if char in string.whitespace:
                
                    # Possible padding.
                    
                    if style.and_operator in string.whitespace:
                    
                        # Ordered AND operation or whitespace.
                        
                        # In order to discover whether this character
                        # represents an operation on labels or just
                        # whitespace, we must look for any following
                        # operators.
                        
                        text = self.read_string( syntax[pos+1:],
                                                 style.operators )
                        
                        if string.find(text, style.eor_operator) == -1:
                        
                            # There are no EOR operators, so this is just
                            # an AND operator.
                            
                            # Update the current placeholder node, removing any
                            # reference to child nodes if there are none, and moving
                            # the labels of any single child nodes up to this level.
                            
                            tree = tree + self.optimise(node)
                        
                            # We create a new node as a sibling of the current
                            # placeholder node.
                            
                            node = []
                        
                            # Update the syntax definition offset.
                            pos = pos + 1 + len(text)
                        
                            # The next item in the sequence must be a label.
                            next = "label"
                        
                        else:
                        
                            # There are EOR operators before the next item
                            # so this space is just padding.
                            
                            # Move the offset in the syntax definition to
                            # point to the first of these.
                            
                            pos = pos + 1 + string.find( text,
                                                style.eor_operator )
                            
                            # We still expect an operator.
                            next = "operator"
                    
                    elif style.eor_operator in string.whitespace:
                    
                        # Ordered EOR operation or whitespace.
                        
                        # In order to discover whether this character
                        # represents an operation on labels or just
                        # whitespace, we must look for any following
                        # operators.
                        
                        text = self.read_string( syntax[pos+1:],
                                                 style.operators )
                        
                        if string.find(text, style.and_operator) == -1:
                        
                            # There are no AND operators, so this is just
                            # an EOR operator.
                            
                            # Leave the current placeholder node as it is so that
                            # more child nodes can be added as alternative labels.
        
                            # Update the syntax definition offset.
                            pos = pos + 1 + len(text)
                            
                            # The next item in the sequence must be a label.
                            next = "label"
                        
                        else:
                        
                            # There are AND operators before the next item
                            # so this space is just padding.
                            
                            # Move the offset in the syntax definition to
                            # point to the first of these.
                            
                            pos = pos + 1 + string.find( text,
                                                style.and_operator )
                            
                            # We still expect an operator.
                            next = "operator"
                    
                    else:
                    
                        # This is just padding.
                        pos = pos + 1
                    
                # Not whitespace, but either AND or EOR operator may be
                # non-whitespace so we still look for them.
                
                # If neither operator is a whitespace character then
                # things are straightforward to deal with:
                
                elif char == style.and_operator:
                
                    # Update the current placeholder node, removing any
                    # reference to child nodes if there are none, and moving
                    # the labels of any single child nodes up to this level.
                    
                    tree = tree + self.optimise(node)
                
                    # We create a new node as a sibling of the current
                    # placeholder node.
                    
                    node = []
                
                    # Update the syntax definition offset.
                    pos = pos + 1 + len(text)
                
                    # The next item in the sequence must be a label.
                    next = "label"
                
                elif char == style.eor_operator:
                
                    # Exclusive OR operation.
                    
                    # Leave the current placeholder node as it is so that
                    # more child nodes can be added as alternative labels.
                    
                    # Update the syntax definition offset.
                    pos = pos + 1
                    
                    # The next item in the sequence must be a label.
                    next = "label"
                
                else:
                
                    raise cmdsyntax_error, \
                          "Expected an operator, but instead found " + \
                          repr(char)+" at offset %i: %s" % (pos, syntax[pos:])
                        
            # No need for an else statement since the if statement catches all
            # other characters.
    
        # The control flow should only reach here at the end the syntax
        # definition. If we are expecting a ] or ) then there is at least
        # one missing.
        
        if end != None:
        
            raise cmdsyntax_error, \
                  "End of syntax definition reached, where "+str(end) + \
                  " was expected."
        
        # If the current node is non-empty then optimise it, and add it to the
        # tree.
        
        tree = tree + self.optimise(node)
        
        # Allow for unordered optional items by converting
        # groups of optional items into a Selection object
        # which chooses between zero and the total number
        # of grouped items.
        tree = self.group_options(tree)
        
        return tree, pos
            
                
    def optimise(self, node):
        """new = optimise(self, node)
        
        Update the node given, removing any reference to child nodes if there
        are none, and moving the labels of any single child nodes up to this
        level.
        """
        
        #print "->", node
        # If the node contains [] or [string] then just return this,
        # as it will be added to the end of the tree at that level.
        if len(node) > 1:
        
            # Place the node dictionary in a list so that it can be added
            # to the existing items in the list for this level.
            
            # We write a node with a number of items in a list as a
            # selection in which only one item can be chosen.
            # However, if one of these items is an empty list then
            # we can simplify the selection to one in which no items
            # may be selected if necessary.
            
            if [] not in node:
            
                # No empty item in this list: one item must be chosen.
                node = [ Selection(node, 1, 1) ]
            
            else:
            
                # An empty item is present: one item at most must be
                # chosen from the rest of the items.
                items = []
                
                for item in node:
                
                    if item != []:
                        items.append(item)
                
                node = [ Selection(items, 0, 1) ]
        
        #print "<-", node
        return node
    
    
    def group_options(self, tree):
    
        # Examine the list representing this level of the syntax tree
        # and if we find groups of optional arguments then reconfigure
        # the syntax tree to allow them to be specified in any order
        # from the command line using a Selection object which requires
        # that between zero and the total number of grouped objects be
        # selected.
        #
        # e.g. infile [-a abacus] [-b binary] outfile [-c computer]
        #
        # allows the options associated with -a and -b to be specified
        # with either -a first or -b first.
        
        new_list = []
        collection = []

        for node in tree:

            # Check whether the node is a Selection object which allows
            # no items to be selected.
            if isinstance(node, Selection) and node.minimum == 0:
            
                # If so, we add this node to our collection.
                collection.append(node)
                
            else:

                # Not an optional argument.
                if collection != []:
                
                    # Create a tree to insert in the new list of nodes
                    # which allows the collected nodes to occur in any
                    # order on the command line.
                    new_list = new_list + self.select_options(collection)
                    
                    collection = []
                    
                # Add the current node to the list.
                new_list.append(node)
        
        # If there are any collected nodes left over then add them now
        # at the end.

        new_list = new_list + self.select_options(collection)

        return new_list
    
    
    def select_options(self, options):
    
        # From the list of optional items, return a Selection object
        # containing a list of Selections for each optional item.
        
        objects = []
        
        # For only one option, 
        if len(options) <= 1:

            # The list of options becomes the list of children.
            return options
        
        for option in options:
        
            # For each option, check whether there is just one
            # optional item or whether there are many possibilities.
            # e.g. [-a] or [-a|-b]
            #
            # For just one possibility, add the item to the list;
            # for more than one, add a selection object to the list
            # requiring that only one item be selected.
            
            if len(option.objects) == 1:
            
                # Include the optional object itself as it will appear
                # in a selection object which does not require any
                # objects to be selected.
                objects.append(option.objects[0])
            
            else:
            
                # There is more than one object to choose between,
                # so if this selection is chosen then only one of these
                # must be selected.
                objects.append( Selection(option.objects, 1) )
            
        # Return a selection object requiring that between zero and the
        # total number of objects be selected.
        return [ Selection(objects, 0) ]
    
    
    def expand_args(self, argv, style):

        # Expand any single dash switches with more than one character.
        
        new_argv = []
        
        for arg in argv:
        
            if len(arg) > 2 and arg[0] == style.switches and \
               arg[1] != style.switches:
            
                # A switch with one dash and more than one following
                # character. Split into a number of single dash, single
                # character switches.
                
                for char in arg[1:]:
                
                    new_argv.append( style.switches + char )
            
            else:
            
                # Just a normal argument.
                new_argv.append( arg )
        
        # Replace the original arguments list.
        return new_argv
    
    
    def match_arguments( self, tree, argv, in_order, style, find_first,
                         matches = None, args = None ):
        """matches = all_permutations( self, tree, argv, in_order, style,
                                       find_first, matches = None, args = None )
        
        Match the command line arguments against the syntax tree.
        
        tree is the syntax tree.
        argv is the list of arguments from the command line.
        
        in_order = 0 allows optional arguments to be specified in any order;
        in_order = 1 forces optional arguments to be specified in the order
        given in the syntax definition.
        
        style is the style in which the command line was written.
        
        find_first = 1 causes the first match to be returned;
        find_first = 0 returns all possible matches.
        
        matches is a list of pairs containing a match dictionary and the
        current location in the command line argument list, argv, for that
        match.
        """
    
        # The current matches and command line cursors.
        if matches == None:
        
            matches = [ {} ]
        
        if args == None:
        
            args = [ 0 ]
        
        for item in tree:
        
            # For each item in the syntax tree we attempt to match a
            # command line argument from each ongoing match.
            new_matches = []
            new_args = []
            
            # Examine each item in this ordered required list of items.
            
            if isinstance(item, Option):
            
                for m in range(len(matches)):
                
                    match = matches[m]
                    arg = args[m]
                
                    if arg < len(argv) and style.is_option(argv[arg]):
                
                        # An Option object, more arguments from the command line
                        # and the next one is an option, too.
                        
                        # Obtain a canonical form for the command line option.
                        cmd_option = style.unstyle_option(argv[arg], 0)
                        
                        # Determine whether the syntax option and the command
                        # line option are of the same form:
                        
                        if item.name == cmd_option.name:
                        
                            # The names match.
                            
                            if item.value == None and cmd_option.value == None:
                        
                                # Both options have the same form and the names
                                # match.
                                
                                # Add the name of the switch to the match
                                # dictionary.
                            
                                match[item.name] = 1
                                
                                #print "Match: %s" % item.name
                                
                                # Copy the dictionary to the new list.
                                new_matches.append(match)
                                
                                # Increment the argument index and copy it
                                # across to the new list.
                                new_args.append(arg + 1)
                        
                            elif item.value != None and cmd_option.value != None:
                            
                                # Both switches take the form <name>=<value> so
                                # read the value and store it in the match
                                # dictionary under the name of the switch.
                                
                                match[item.name] = cmd_option.value
                                
                                #print "Match: %s = %s" % (item.name, cmd_option.value)
                                
                                # Copy the dictionary to the new list.
                                new_matches.append(match)
                                
                                # Increment the argument index and copy it
                                # across to the new list.
                                new_args.append(arg + 1)
                
                # Some matches must survive in order for matching to continue.
                if new_matches == []:
                
                    # No matches were found for this item.
                    return [], args
            
            elif type(item) == types.StringType:
            
                for m in range(len(matches)):
                
                    match = matches[m]
                    arg = args[m]
                
                    if arg < len(argv):
                    
                        # An ordinary argument which is represented by a
                        # label in the syntax definition.
                        
                        # Put an entry in the match dictionary under the
                        # name given in the syntax definition.
                        
                        match[item] = argv[arg]
                        
                        # Copy the dictionary to the new list.
                        new_matches.append(match)
                        
                        # Move to the next command line argument.
                        new_args.append(arg + 1)
            
                # Some matches must survive in order for matching to continue.
                if new_matches == []:
                
                    # No matches were found for this item.
                    return [], args
            
            elif isinstance(item, Command):
                
                for m in range(len(matches)):
                
                    match = matches[m]
                    arg = args[m]
                
                    # A string which must be matched with the user
                    # input from the command line.
                    
                    if arg < len(argv) and item.name == argv[arg]:
                    
                        # Add the command string to the match
                        # dictionary.
                        match[item.name] = 1
                    
                        # Copy the dictionary to the new list.
                        new_matches.append(match)
                        
                        # Move to the next command line argument.
                        new_args.append(arg + 1)
                
                # Some matches must survive in order for matching to continue.
                if new_matches == []:
                
                    # No matches were found for this item.
                    return [], args
            
            elif isinstance(item, Selection):
            
                # The children are exclusive, so we pass each match
                # dictionary and position in the command line arguments
                # to each child.
                # Each non-None result will be added to the match
                # dictionary and copied across to the list of new matches
                # and the new command line position will be copied
                # to the new list of command line positions.
                
                if matches != [] and item.maximum > 0:
                
                    for s in range(len(item.objects)):
                    
                        # Select this item but keep the other items in the
                        # Selection optional
                        # Copy the lists of matches and argument numbers
                        # to avoid the originals being modified.
                        # The list of dictionaries is deep copied.
                        
                        add_matches, add_args = self.match_arguments(
                            [item.objects[s]], argv, in_order, style, find_first,
                            copy.deepcopy(matches), copy.copy(args) )
                        
                        if add_matches != []:
                        
                            # A list was returned (success).
                            
                            # Copy each element into the new list of matches.
                            new_matches = new_matches + add_matches
                            new_args = new_args + add_args
                            
                            try:
                            
                                # Continue to match against subsequent arguments.
                                # Recurse with the remaining selection items.
                                
                                if in_order == 1:
                                
                                    new_select = Selection( item.objects[s+1:],
                                                     max(0, item.minimum - 1),
                                                     max(item.maximum - 1, 0) )
                                else:
                                    new_select = Selection(
                                                     item.objects[s+1:] + \
                                                     item.objects[:s],
                                                     max(0, item.minimum - 1),
                                                     max(item.maximum - 1, 0) )
                                
                                add_matches, add_args = self.match_arguments(
                                    [ new_select ],
                                    argv, in_order, style, find_first,
                                    copy.deepcopy(add_matches),
                                    copy.copy(add_args) )
                                
                                if add_matches != []:
                                
                                    # Copy each element into the new list of matches.
                                    new_matches = new_matches + add_matches
                                    new_args = new_args + add_args

                            except cmdsyntax_error:
                            
                                # The maximum number of selections was
                                # reached.
                                pass
                            
                            # Also, ignore this particular match and recurse
                            # with the remaining arguments.
                            
                            if in_order == 1:
                            
                                add_matches, add_args = self.match_arguments(
                                    [
                                      Selection( item.objects[s+1:],
                                                 item.minimum,
                                                 item.maximum )
                                    ],
                                    argv, in_order, style, find_first,
                                    copy.deepcopy(matches),
                                    copy.copy(args) )
                            else:
                                add_matches, add_args = self.match_arguments(
                                    [
                                      Selection( item.objects[s+1:] + \
                                                 item.objects[:s],
                                                 item.minimum,
                                                 item.maximum )
                                    ],
                                    argv, in_order, style, find_first,
                                    copy.deepcopy(matches),
                                    copy.copy(args) )
                            
                            if add_matches != []:
                            
                                # Copy each element into the new list of matches.
                                new_matches = new_matches + add_matches
                                new_args = new_args + add_args
                        
                        else:
                        
                            # The selection item did not match the command line
                            # argument.
                            pass
                        
                
                # If the Selection allows no objects to be selected
                # then we may also add the original lists of matches and
                # command line argument locations.
                
                if item.minimum == 0:
                
                    new_matches = new_matches + matches
                    new_args = new_args + args
                
                if new_matches == []:
                
                    # No permutation matched the command line.
                    return [], args
                    
            elif type(item) == types.ListType:
            
                if item != []:
                
                    # A collection of items: recurse.
                    new_matches, new_args = self.match_arguments(
                                                item, argv, in_order, style,
                                                find_first,
                                                copy.copy(matches),
                                                copy.copy(args) )
                    
                    if new_matches == []:
                    
                        # No matches were found from this collection.
                        return [], args
                
                else:
                
                    # Empty item: we do not have to match anything against
                    # this.
                    pass
        
            # Replace the old match dictionary and argument dictionary
            # with the new ones.
            
            # Remove duplicate entries in the matches and args lists.
            matches = []
            args = []
            
            for m in range(len(new_matches)):
            
                if new_matches[m] not in matches:
                
                    matches.append(new_matches[m])
                    args.append(new_args[m])
        
        # Return the match.
        return matches, args
    
    
    def create_argv(self, text):
        """argv = create_argv(self, text)
        Create an argument list from a text string for use in the matching
        methods.
        """
        
        argv = []
        
        # Read the string, splitting it at spaces and keeping quoted text
        # together.
        arg = ""
        
        i = 0
        while i < len(text):
        
            char = text[i]
            
            if char == '"':
            
                # Quoted text.
                quoted = self.read_string(text[i:], None, '"')
                arg = arg + quoted
                i = i + len(quoted)

            elif char in string.whitespace:
            
                # Argument separator space.
                argv.append(arg)
                arg = ""
                i = i + 1

            else:
            
                # Non-whitespace and non quoted character.
                arg = arg + char
                i = i + 1
                
        if arg != "":
        
            argv.append(arg)

        return argv


# Classes for constructing GUI forms based on syntax definitions.

class form_error(Exception):

    pass


def use_GUI(prefer = None):
    """toolkit = use_GUI(prefer = None)
    Check which GUI toolkits are available to display forms.
    
    prefer can be "Tkinter" for the Tkinter toolkit or None for no
    preference.
    
    The name of the toolkit which will be used is returned, or None if
    no toolkits are available.
    """
    
    global toolkit
    
    toolkit = None
    
    if prefer == "PyQt":
    
        # Try to import PyQt.
        try:
        
            global qt
            import qt
            toolkit = "PyQt"
        
        except ImportError:
        
            pass
    
    # Fallback to using Tkinter
    if toolkit == None:
    
        # Try to import Tkinter.
        try:
        
            global Tkinter
            import Tkinter
            toolkit = "Tkinter"
        
        except ImportError:
    
            pass

    return toolkit


class Form:
    """form = Form(name, syntax)
    Create a graphical form with input fields required by the syntax definition.
    The name given is displayed in the window's title bar.
    """
    def __init__(self, name, syntax):
    
        # Use the toolkit variable to determine the class to use.
        if toolkit == "PyQt":
        
            self.form = QtForm(name, syntax)
        
        elif toolkit == "Tkinter":
        
            self.form = TkForm(name, syntax)
        
        else:
        
            raise form_error, "GUI not set up correctly with use_GUI function."
    
    def get_args(self):
        """dict = get_args(self)
        Return a dictionary containing the values given by the user in the
        same form to the dictionaries returned from the Syntax.get_args
        method.
        """
        return self.form.get_args()


# Tkform - A form for the Tkinter module using the Tk GUI toolkit
#
# Note that this is inspired and based on Fredrik Lundh's ScrolledFrame
# example widget:
#
# http://mail.python.org/pipermail/python-list/1999-October/013255.html

class TkForm:

    def __init__(self, name, syntax):
    
        # Create a Tkinter form from the syntax object given.
        # This could be done automatically if the programmer checked for no
        # input at the start of the program.
        
        # Define the form contents.
        self.contents = {}
        
        # Define an error message to be filled in if a match fails.
        self.error = ""
        
        # Create a window to contain everything.
        self.window = Tkinter.Tk()
        
        # Give the window a name.
        self.window.title(name)
        
        # Add two buttons at the bottom of the form.
        button_frame = Tkinter.Frame(self.window)
        
        ok = Tkinter.Button( button_frame, text = "OK",
                             command = self.read_form )
        
        ok.grid(column = 0, row = 0, padx = 8)
        
        cancel = Tkinter.Button( button_frame, text = "Cancel",
                                 command = self.close_form )
        
        cancel.grid(column = 1, row = 0, padx = 8)
        
        button_frame.pack( side = Tkinter.BOTTOM, fill = Tkinter.BOTH,
                           pady = 16 )
        
        # Create a vertical scrollbar.
        self.scrollbar = Tkinter.Scrollbar( self.window )
        
        # Create a Canvas widget to contain the structure.
        self.canvas = Tkinter.Canvas( self.window,
                                      yscrollcommand = self.scrollbar.set,
                                      borderwidth = 1,
                                      relief = Tkinter.SUNKEN )
        
        # Configure the scrollbar.
        self.scrollbar.config( command = self.canvas.yview )
        
        # Put the scrollbar on the right of the window.
        self.scrollbar.pack( side = Tkinter.RIGHT, fill = Tkinter.BOTH )
        
        # Put the canvas on the left of the window.
        self.canvas.pack( expand = 1, side = Tkinter.LEFT, fill = Tkinter.BOTH )
        
        # Set the scroll offsets for the canvas.
        self.canvas.xview(Tkinter.MOVETO, 0)
        self.canvas.yview(Tkinter.MOVETO, 0)
        
        # Create a Frame object to go on the canvas.
        self.frame = Tkinter.Frame(self.canvas)
        
        # Put the structure frame in the canvas.
        self.canvas.create_window( 0, 0, window = self.frame,
                                   anchor = Tkinter.NW )
        
        # Bind a configure method to the Frame.
        self.frame.bind("<Configure>", self.configure)
        
        # Create a list of objects for the frame.
        self.frame._cmdsyntax_ = []
        
        # Traverse the syntax tree and add widgets to the window.
        self.add_widgets(self.frame, syntax.syntax_tree)
        
        # Start the event loop.
        self.window.mainloop()
    
    
    def configure(self, event):
    
        w, h = self.frame.winfo_reqwidth(), self.frame.winfo_reqheight()
        self.canvas.config( scrollregion = (0, 0, w, h) )
        self.canvas.config( width = w )
    
    
    def get_args(self):
    
        # Return the form contents if present.
        if self.error != "":
        
            return {}
        
        else:
        
            return self.contents
    
    
    def add_widgets(self, widget, syntax, row = 0):
    
        for item in syntax:
        
            # Examine each item in this ordered required list of items.
            
            if isinstance(item, Option):
            
                # Use a Label for "optional" switch arguments.
                if item.value == None:
                
                    # A single option: use the option name for the checkbutton
                    # text.
                    label = Tkinter.Label( widget, text = item.name )
                
                    # Store the actual option name in the Label object.
                    label._cmdsyntax_ = item.name
                    label.grid( row = row, sticky = Tkinter.W, padx = 2,
                                pady = 2 )
                
                    # Put the Label in the list of relevant objects in the
                    # parent widget.
                    widget._cmdsyntax_.append(label)
                
                else:
                
                    # An name=value pair. The name will usually be more
                    # descriptive, so use that for the Label text.
                    label = Tkinter.Label( widget, text = item.name )
                    label.grid( row = row, column = 0, sticky = Tkinter.W,
                                padx = 2, pady = 2 )
                    
                    # Add an Entry object next to the label.
                    entry = Tkinter.Entry(widget)
                    entry.grid( column = 1, row = row, sticky = Tkinter.W,
                                padx = 2, pady = 2 )
        
                    # Store the item name in the Entry object.
                    entry._cmdsyntax_ = item.name
                    
                    # Put the Entry in the list of relevant objects in the
                    # parent widget.
                    widget._cmdsyntax_.append(entry)
                
                row = row + 1
            
            elif type(item) == types.StringType:
            
                # An ordinary argument which is represented by a
                # label in the syntax definition.
                
                # Add a Label object with the label in the syntax definition as
                # the label text.
                label = Tkinter.Label(widget, text = item)
                label.grid( column = 0, row = row, sticky = Tkinter.W, padx = 2,
                            pady = 2 )
                
                # Add an Entry object next to the label.
                entry = Tkinter.Entry(widget)
                entry.grid( column = 1, row = row, sticky = Tkinter.W, padx = 2,
                            pady = 2 )
    
                # Store the item name in the Entry object.
                entry._cmdsyntax_ = item
    
                # Put the Entry object in the list of relevant objects in the
                # parent widget.
                widget._cmdsyntax_.append(entry)
    
                row = row + 1
            
            elif isinstance(item, Command):
                
                # A command argument which must occur.
                
                # Add a Label object with the command in the syntax definition
                # as the label text.
                label = Tkinter.Label(widget, text = item.name)
                label.grid(row = row, sticky = Tkinter.W, padx = 2, pady = 2)
                
                # Store the item name in the Label object.
                label._cmdsyntax_ = item.name
                
                # Put the Label object in the list of relevant objects in the
                # parent widget.
                widget._cmdsyntax_.append(label)

                row = row + 1
            
            elif isinstance(item, Selection) and item.objects != []:
            
                # Although the children are exclusive, we can just display
                # them all and let invalid input be caught later.
                
                # We can catch selection of each of these objects and shade
                # the other members in this selection group.
                
                # Create a parent frame for the selection and a label indicating
                # the number of objects to be selected.
                selection = Tkinter.Frame( widget )
                
                # Create a list of objects for the frame.
                selection._cmdsyntax_ = []
                
                # Store the number of choices which must be made.
                selection._cmdsyntax_min_ = item.minimum
                selection._cmdsyntax_max_ = item.maximum
                
                choice_text = self.write_choice_text(
                    item.minimum, item.maximum, len(item.objects) )
                
                # Give the selection frame a label containing the number of 
                # options to choose assuming that there will only be two
                # columns in the selection widget.
                label = Tkinter.Label(selection, text = choice_text)
                label.grid(row = 0, columnspan = 2)
                
                select_row = 1
                
                # A collection of items: create a button and a frame widget for
                # each and recurse.
                for object in item.objects:
                
                    # Add a button for this new frame.
                    
                    # Create a variable to hold the state of the button.
                    bvar = Tkinter.IntVar()
                    
                    button = Tkinter.Checkbutton( selection, text = "",
                                                  variable = bvar )
                    
                    # Store the variable inside the Checkbutton object.
                    button._cmdsyntax_var_ = bvar
                    
                    button.grid( row = select_row, column = 0, padx = 2,
                                 sticky = Tkinter.NW )
                    
                    # Put the Checkbutton object in the list of relevant objects
                    # in the parent widget.
                    selection._cmdsyntax_.append(button)
                    
                    
                    # Create the frame.
                    
                    frame = Tkinter.Frame( selection, borderwidth = 1,
                                           relief = Tkinter.SUNKEN )
                    
                    # Create a list of objects for the frame.
                    frame._cmdsyntax_ = []
                    
                    self.add_widgets(frame, [object])
                    
                    frame.grid( row = select_row, column = 1, padx = 4,
                                pady = 4, sticky = Tkinter.W )
                    
                    # Put the Frame object in the list of relevant objects
                    # in the parent widget.
                    selection._cmdsyntax_.append(frame)
                    
                    select_row = select_row + 1
                
                
                # Lay out the selection frame assuming that there will only
                # be two columns in the parent widget.
                selection.grid( row = row, sticky = Tkinter.W, columnspan = 2,
                                padx = 4, pady = 4 )
    
                # Put the Frame object in the list of relevant objects in the
                # parent widget.
                widget._cmdsyntax_.append(selection)
                
                row = row + 1
            
            elif type(item) == types.ListType and item != []:
            
                # A collection of items: create a frame widget and recurse.
    
                frame = Tkinter.Frame( widget )
                
                # Create a list of objects for the frame.
                frame._cmdsyntax_ = []
                
                self.add_widgets(frame, item)
    
                # Lay out the selection frame assuming that there will only
                # be two columns in the parent widget.
                frame.grid( row = row, columnspan = 2, padx = 4, pady = 4,
                            sticky = Tkinter.W )
                
                # Put the Frame object in the list of relevant objects in the
                # parent widget.
                widget._cmdsyntax_.append(frame)
                
                row = row + 1


    def write_choice_text(self, mini, maxi, total):
    
        if total > 1:
        
            if mini != maxi:
            
                if mini > 0:
                
                    choice_min = "from %i" % mini
                    
                    if maxi != total:
                    
                        choice_max = "to %i of" % maxi
                    
                    else:
                    
                        choice_max = "of"
                
                else:
                    choice_min = ""
                    
                    if maxi != total and maxi > 1:
                    
                        choice_max = "up to %i of" % maxi
                    
                    elif maxi != total and maxi == 1:
                    
                        choice_max = "%i of" % maxi
                    
                    else:
                    
                        choice_max = "any of"
                        
            else:
            
                if mini != total:
                
                    choice_min = "%i from" % mini
                
                else:
                
                    choice_min = "any of"
                
                choice_max = ""
            
            
            choice_min_max = "%s %s" % \
                (string.strip(choice_min), string.strip(choice_max))
            
            text = "Select %s the following %i options:" % \
                (string.strip(choice_min_max), total)
            
        else:
        
            # Special case of only one option.
            
            if mini == 0 and maxi == 0:
            
                # Unlikely.
                text = "Do not select this option:"
            
            elif mini == 0 and maxi != 0:
            
                text = "Optionally select the following item:"
        
            elif mini != 0 and maxi != 0:
            
                # Unlikely: any Selection with minimum = maximum = total
                # should never have been created. A list should have been
                # created instead.
                text = "You must select this option:"
            
            else:
            
                # Another unlikely scenario.
                text = "Impossible selection:"
        
        return text
    
    
    def read_form(self, widget = None):
    
        # Examine each widget within the main form widget, extracting the
        # data contained in those which have a _cmdsyntax_ attribute.
    
        if widget == None:
        
            widget = self.frame
        
        if hasattr(widget, "_cmdsyntax_"):
        
            # The widget contains information relevant to the required syntax.
            
            if isinstance(widget, Tkinter.Label):
            
                # This is usually used for Option and Command objects, so
                # create a dictionary entry using the hidden information
                # as a key and give it an arbitrary value of one to indicate
                # its presence.
                self.contents[widget._cmdsyntax_] = 1
            
            elif isinstance(widget, Tkinter.Entry):
            
                # This is used as a label placeholder.
                # Use the hidden information as the dictionary key and the
                # widget's value as the dictionary entry's value.
                self.contents[widget._cmdsyntax_] = widget.get()
            
            elif isinstance(widget, Tkinter.Canvas):
            
                # Just an ordinary grouping of options.
                
                # Examine each widget in turn.
                for object in widget._cmdsyntax_:
                
                    self.read_form(object)
            
            elif isinstance(widget, Tkinter.Frame):
            
                if hasattr(widget, "_cmdsyntax_min_"):
                
                    # A Selection object is being represented.
                    
                    # The objects in the _cmdsyntax_ list will be
                    # Checkbuttons followed by Frames.
                    
                    # Examine the Checkbuttons and determine whether
                    # the correct number have been selected.
                    
                    checked = 0
                    
                    for i in range(0, len(widget._cmdsyntax_), 2):
                    
                        button = widget._cmdsyntax_[i]
                        
                        if button._cmdsyntax_var_.get() == Tkinter.ON:
                        
                            checked = checked + 1
                    
                    if checked < widget._cmdsyntax_min_ or \
                       checked > widget._cmdsyntax_max_:
                    
                        # The number of Checkbuttons selected was
                        # outside the range expected.
                        
                        # We can't raise an exception as Tkinter
                        # will suppress it so set an error message
                        # as well.
                        
                        self.error = "The number of Checkbuttons" + \
                            " clicked was outside the range expected."
                        
                        #raise matching_error, \
                        #    "The number of Checkbuttons clicked was" + \
                        #    " outside the range expected."
                    
                    # Read the Frames associated with the selected
                    # Checkbuttons.
                    
                    for i in range(0, len(widget._cmdsyntax_), 2):
                    
                        button = widget._cmdsyntax_[i]
                        
                        if button._cmdsyntax_var_.get() == Tkinter.ON:
                        
                            # Everything is in order. Examine the Frame
                            # object after the Checkbutton.
                            self.read_form(widget._cmdsyntax_[i+1])
                
                else:
                
                    # Just an ordinary grouping of options.
                    
                    # Examine each widget in turn.
                    for object in widget._cmdsyntax_:
                    
                        self.read_form(object)
        
        # Close the window.
        self.frame.quit()
    
    
    def close_form(self):
    
        self.frame.quit()


# QtForm - A form for the PyQt module using the Qt GUI toolkit

class QtForm:

    def __init__(self, name, syntax):
    
        # Create a PyQt form from the syntax object given.
        # This could be done automatically if the programmer checked for no
        # input at the start of the program.
        
        # Define the form contents.
        self.contents = {}
        
        # Define an error message to be filled in if a match fails.
        self.error = ""
        
        # Start a Qt application.
        self.app = qt.QApplication( [] )
        
        # Create a window to contain everything.
        window = qt.QWidget()
        
        # Give the window a name.
        window.setCaption(name)
        
        # Make this window the main window for the application (closing it will
        # cause the event loop to be exited.
        self.app.setMainWidget(window)
        
        # Add a layout manager for the window.
        layout = qt.QGridLayout(window, 0, 0, 4)
        
        # Create a QScrollView widget to contain the structure frame.
        scrollview = qt.QScrollView(window, "", qt.Qt.WNorthWestGravity )
        
        # Place the frame in the window.
        layout.addWidget(scrollview, 0, 0)
        
        # Create a structure frame to contain all the widgets.
        self.frame = qt.QFrame(scrollview)
        
        # Place the frame in the QScrollView.
        scrollview.addChild(self.frame, 0, 0)
        
        # Create a list of objects for the frame.
        self.frame._cmdsyntax_ = []
        
        # Add a layout manager to this frame.
        frame_layout = qt.QGridLayout(self.frame, 0, 0, 4, 2)
        
        # Traverse the syntax tree and add widgets to the window.
        self.add_widgets(self.frame, frame_layout, syntax.syntax_tree)
        
        # Add two buttons at the bottom of the form.
        button_frame = qt.QFrame( window )
        
        button_layout = qt.QGridLayout(button_frame, 0, 0, 4, 2)
        
        ok = qt.QPushButton("OK", button_frame)
        button_layout.addWidget( ok, 0, 0, qt.Qt.AlignCenter )
        
        # Connect the clicked signal from this button to the read_form
        # method of this class.
        qt.QObject.connect( ok, qt.SIGNAL("clicked()"), self.read_form )
        
        cancel = qt.QPushButton("Cancel", button_frame)
        button_layout.addWidget( cancel, 0, 1, qt.Qt.AlignCenter )
        
        # Connect the clicked signal from this button to the quit slot of
        # the application.
        qt.QObject.connect( cancel, qt.SIGNAL("clicked()"), self.close_form )
        
        # Add the button QFrame to the window layout.
        layout.addWidget( button_frame, 1, 0 )
        
        # Give more emphasis to the QScrollView widget in the layout.
        layout.setRowStretch(0, 1)
        
        # Show the window.
        window.show()
        
        # Start the event loop.
        self.app.exec_loop()
    
    
    def get_args(self):
    
        # Return the form contents if present.
        if self.error != "":
        
            return {}
        
        else:
        
            return self.contents
    
    
    def add_widgets(self, widget, layout, syntax, row = 0):
    
        for item in syntax:
        
            # Examine each item in this ordered required list of items.
            
            if isinstance(item, Option):
            
                # Use a Label for "optional" switch arguments.
                if item.value == None:
                
                    # A single option: use the option name for the checkbutton
                    # text.
                    label = qt.QLabel( item.name, widget )
                
                    # Store the actual option name in the Label object.
                    label._cmdsyntax_ = item.name
                    layout.addWidget( label, row, 0, qt.Qt.AlignLeft )
                
                    # Put the QLabel in the list of relevant objects in the
                    # parent widget.
                    widget._cmdsyntax_.append(label)
                
                else:
                
                    # An name=value pair. The name will usually be more
                    # descriptive, so use that for the Label text.
                    label = qt.QLabel( item.name, widget )
                    layout.addWidget( label, row, 0, qt.Qt.AlignLeft )
                    
                    # Add a QLineEdit object next to the label.
                    entry = qt.QLineEdit(widget)
                    layout.addWidget( entry, row, 1, qt.Qt.AlignLeft )
        
                    # Store the item name in the QLineEdit object.
                    entry._cmdsyntax_ = item.name
                    
                    # Put the QLineEdit in the list of relevant objects in the
                    # parent widget.
                    widget._cmdsyntax_.append(entry)
                
                row = row + 1
            
            elif type(item) == types.StringType:
            
                # An ordinary argument which is represented by a
                # label in the syntax definition.
                
                # Add a QLabel object with the label in the syntax definition as
                # the label text.
                label = qt.QLabel( item, widget )
                layout.addWidget( label, row, 0, qt.Qt.AlignLeft )
                
                # Add an QLineEdit object next to the label.
                entry = qt.QLineEdit(widget)
                layout.addWidget( entry, row, 1, qt.Qt.AlignLeft )
    
                # Store the item name in the QLineEdit object.
                entry._cmdsyntax_ = item
    
                # Put the QLineEdit object in the list of relevant objects in the
                # parent widget.
                widget._cmdsyntax_.append(entry)
    
                row = row + 1
            
            elif isinstance(item, Command):
                
                # A command argument which must occur.
                
                # Add a QLabel object with the command in the syntax definition
                # as the label text.
                label = qt.QLabel( item.name, widget )
                layout.addWidget( label, row, 0, qt.Qt.AlignLeft )
                
                # Store the item name in the QLabel object.
                label._cmdsyntax_ = item.name
                
                # Put the QLabel object in the list of relevant objects in the
                # parent widget.
                widget._cmdsyntax_.append(label)

                row = row + 1
            
            elif isinstance(item, Selection) and item.objects != []:
            
                # Although the children are exclusive, we can just display
                # them all and let invalid input be caught later.
                
                # We can catch selection of each of these objects and shade
                # the other members in this selection group.
                
                # Create a parent frame for the selection and a label indicating
                # the number of objects to be selected.
                selection = qt.QFrame( widget )
                
                # Use a layout manager for this frame.
                select_layout = qt.QGridLayout( selection, 0, 0, 4, 8 )
                
                # Create a list of objects for the frame.
                selection._cmdsyntax_ = []
                
                # Store the number of choices which must be made.
                selection._cmdsyntax_min_ = item.minimum
                selection._cmdsyntax_max_ = item.maximum
                
                choice_text = self.write_choice_text(
                    item.minimum, item.maximum, len(item.objects) )
                
                # Give the selection frame a label containing the number of 
                # options to choose assuming that there will only be two
                # columns in the selection widget.
                label = qt.QLabel( choice_text, selection )
                
                select_layout.addMultiCellWidget( label, 0, 0, 0, 1 )
                #select_layout.setColStretch(0, 1)
                
                select_row = 1
                
                # A collection of items: create a button and a frame widget for
                # each and recurse.
                for object in item.objects:
                
                    # Add a button for this new frame.
                    button = qt.QCheckBox( selection, "" )
                    
                    select_layout.addWidget( button, select_row, 0, qt.Qt.AlignLeft | qt.Qt.AlignTop )
                    
                    # Put the Checkbutton object in the list of relevant objects
                    # in the parent widget.
                    selection._cmdsyntax_.append(button)
                    
                    
                    # Create the frame.
                    
                    frame = qt.QFrame(selection)
                    frame.setFrameStyle( qt.QFrame.Panel | qt.QFrame.Sunken )
                    
                    # Use a layout manager for the frame.
                    frame_layout = qt.QGridLayout( frame, 0, 0, 4, 2 )
                    
                    # Create a list of objects for the frame.
                    frame._cmdsyntax_ = []
                    
                    self.add_widgets(frame, frame_layout, [object])
                    
                    select_layout.addWidget( frame, select_row, 1 )
                    
                    # Put the Frame object in the list of relevant objects
                    # in the parent widget.
                    selection._cmdsyntax_.append(frame)
                    
                    select_row = select_row + 1
                
                
                # Lay out the selection frame assuming that there will only
                # be two columns in the parent widget.
                layout.addMultiCellWidget( selection, row, row, 0, 1,
                                           qt.Qt.AlignLeft )
    
                # Put the Frame object in the list of relevant objects in the
                # parent widget.
                widget._cmdsyntax_.append(selection)
                
                row = row + 1
            
            elif type(item) == types.ListType and item != []:
            
                # A collection of items: create a frame widget and recurse.
    
                frame = qt.QFrame( widget )
                
                # Use a layout manager for the frame.
                frame_layout = qt.QGridLayout(frame, 0, 0, 4, 2)
                
                # Create a list of objects for the frame.
                frame._cmdsyntax_ = []
                
                self.add_widgets(frame, frame_layout, item)
    
                # Lay out the selection frame assuming that there will only
                # be two columns in the parent widget.
                layout.addMultiCellWidget( frame, row, row, 0, 1 )
                
                # Put the Frame object in the list of relevant objects in the
                # parent widget.
                widget._cmdsyntax_.append(frame)
                
                row = row + 1


    def write_choice_text(self, mini, maxi, total):
    
        if total > 1:
        
            if mini != maxi:
            
                if mini > 0:
                
                    choice_min = "from %i" % mini
                    
                    if maxi != total:
                    
                        choice_max = "to %i of" % maxi
                    
                    else:
                    
                        choice_max = "of"
                
                else:
                    choice_min = ""
                    
                    if maxi != total and maxi > 1:
                    
                        choice_max = "up to %i of" % maxi
                    
                    elif maxi != total and maxi == 1:
                    
                        choice_max = "%i of" % maxi
                    
                    else:
                    
                        choice_max = "any of"
                        
            else:
            
                if mini != total:
                
                    choice_min = "%i from" % mini
                
                else:
                
                    choice_min = "any of"
                
                choice_max = ""
            
            
            choice_min_max = "%s %s" % \
                (string.strip(choice_min), string.strip(choice_max))
            
            text = "Select %s the following %i options:" % \
                (string.strip(choice_min_max), total)
            
        else:
        
            # Special case of only one option.
            
            if mini == 0 and maxi == 0:
            
                # Unlikely.
                text = "Do not select this option:"
            
            elif mini == 0 and maxi != 0:
            
                text = "Optionally select the following item:"
        
            elif mini != 0 and maxi != 0:
            
                # Unlikely: any Selection with minimum = maximum = total
                # should never have been created. A list should have been
                # created instead.
                text = "You must select this option:"
            
            else:
            
                # Another unlikely scenario.
                text = "Impossible selection:"
        
        return text
    
    
    def read_form(self, widget = None):
    
        # Examine each widget within the main form widget, extracting the
        # data contained in those which have a _cmdsyntax_ attribute.
    
        if widget == None:
        
            widget = self.frame
        
        if hasattr(widget, "_cmdsyntax_"):
        
            # The widget contains information relevant to the required syntax.
            
            if isinstance(widget, qt.QLabel):
            
                # This is usually used for Option and Command objects, so
                # create a dictionary entry using the hidden information
                # as a key and give it an arbitrary value of one to indicate
                # its presence.
                self.contents[widget._cmdsyntax_] = 1
            
            elif isinstance(widget, qt.QLineEdit):
            
                # This is used as a label placeholder.
                # Use the hidden information as the dictionary key and the
                # widget's value as the dictionary entry's value.
                self.contents[widget._cmdsyntax_] = widget.text().latin1()
            
            elif isinstance(widget, qt.QScrollView):
            
                # Just an ordinary grouping of options.
                
                # Examine each widget in turn.
                for object in widget._cmdsyntax_:
                
                    self.read_form(object)
            
            elif isinstance(widget, qt.QFrame):
            
                if hasattr(widget, "_cmdsyntax_min_"):
                
                    # A Selection object is being represented.
                    
                    # The objects in the _cmdsyntax_ list will be
                    # Checkbuttons followed by Frames.
                    
                    # Examine the Checkbuttons and determine whether
                    # the correct number have been selected.
                    
                    checked = 0
                    
                    for i in range(0, len(widget._cmdsyntax_), 2):
                    
                        button = widget._cmdsyntax_[i]
                        
                        if button.isChecked():
                        
                            checked = checked + 1
                    
                    if checked < widget._cmdsyntax_min_ or \
                       checked > widget._cmdsyntax_max_:
                    
                        # The number of Checkbuttons selected was
                        # outside the range expected.
                        
                        # We can't raise an exception as Tkinter
                        # will suppress it so set an error message
                        # as well.
                        
                        self.error = "The number of Checkbuttons" + \
                            " clicked was outside the range expected."
                        
                        #raise matching_error, \
                        #    "The number of Checkbuttons clicked was" + \
                        #    " outside the range expected."
                    
                    # Read the Frames associated with the selected
                    # Checkbuttons.
                    
                    for i in range(0, len(widget._cmdsyntax_), 2):
                    
                        button = widget._cmdsyntax_[i]
                        
                        if button.isChecked():
                        
                            # Everything is in order. Examine the Frame
                            # object after the Checkbutton.
                            self.read_form(widget._cmdsyntax_[i+1])
                
                else:
                
                    # Just an ordinary grouping of options.
                    
                    # Examine each widget in turn.
                    for object in widget._cmdsyntax_:
                    
                        self.read_form(object)
        
        # Close the window.
        self.app.quit()
    
    
    def close_form(self):
    
        self.app.quit()

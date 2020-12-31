"""
Module containing general utilities for handling lisp-like data. This is the primary form of representation in the 
SMT-Lib 2.6 format that specifies the input format of files given to a SMT solvers.  

This module in particular provides support for handling lisp-like strings where utterances are separated by 
whitespaces and applications are grouped by parentheses. At the level of abstraction provided by this module, 
utterances are themselves simply strings with no additional semantic annotations. The grammar describing such 
'lisp-like' expressions (LL_EXP) is:  

LL_EXP -> (LL_EXP LL_EXP LL_EXP .... LL_EXP)  
LL_EXP -> UTTERANCE  
LL_EXP -> WHITESPACE LL_EXP WHITESPACE  
UTTERANCE -> string  
WHITESPACE -> any of {'\n', ' ', '\t'}  

The module provides functions for reading such lisp-like strings into a nested list of utterances, as well as other 
miscellaneous utilities like pretty printers.  
"""

# TODO (low): give helpful error messages from parser
# TODO (low): integrate/replace parser with official sygus parser


def parser(input_str, noerr=False):
    """
    Basic lisp-like parser.  
    Setting the noerr argument does not raise an exception, instead behaves like a best-effort parser.  
    :param input_str: string  
    :param noerr: bool  
    :return: nested list of strings  
    """
    # Preprocess: remove arbitrary whitespaces and replace with single space
    processed_str = ' '.join(input_str.split())
    # Call a nested list parser that returns nested list of strings
    [nested_list_repr], pos = _parser_aux(processed_str, noerr, len(processed_str))
    # The last parsed position must be the last position
    if pos != len(processed_str) - 1 and not noerr:
        raise ValueError('Input is not lisp-like. Could not parse {}'.format(processed_str[pos+1:]))
    return nested_list_repr


def _parser_aux(in_str, noerr, end, begin=0):
    """
    Simple function to parse lisp-like strings where the delimiters are single spaces.  
    The function returns a 'partially' parsed nested list and an integer, where the integer denotes the position 
    in the input string until which the partial parsing was done. The nested list of strings is such that 
    the leaves are utterances and applications are written as lists of utterances or other lists.  

    Setting the noerr argument does not raise an exception, instead behaves like a best-effort parser.  

    :param in_str: string  
    :param noerr: bool  
    :param end: int (ending position until which the parsing must be done)  
    :param begin: int (the starting position from which the parsing must begin)  
    :return: (nested list of strings, int)  
    """
    # TODO (high): replace this function with an iterative implementation or a library call.
    utterance_accumulator = ''
    partial_result = []
    # Loop character-by-character and recurse when parentheses are opened.
    curr = begin
    while curr < end:
        c = in_str[curr]
        if c == ')':
            # End parsing and pop up the recursion level
            if utterance_accumulator != '':
                partial_result.append(utterance_accumulator)
            return partial_result, curr
        elif c == '(':
            # Recursive call
            # Recursive call can only be made if there are no utterances to be parsed at this point
            if utterance_accumulator != '' and not noerr:
                raise ValueError('Input is not lisp-like. Utterance {} is not part of any expression.'.format(utterance_accumulator))
            partial_repr, partial_pos = _parser_aux(in_str, noerr, end=end, begin=curr+1)
            partial_result.append(partial_repr)
            # Update curr to last parsed position, which is partial_pos
            curr = partial_pos
            # If recursion has ended at topmost level, simply return the result.
            # This prevents from parsing multiple concatenated lisp-like strings, instead parsing only the first one.
            # At topmost level, begin = 0
            if begin == 0:
                return partial_result, curr
        elif c == ' ':
            # Start new utterance if one already exists in the accumulator
            if utterance_accumulator != '':
                partial_result.append(utterance_accumulator)
            utterance_accumulator = ''
        else:
            utterance_accumulator = utterance_accumulator + c

        # Advance curr by one 
        curr = curr + 1
    # Function should not reach this point at the topmost level.
    # If that happens, there is probably an extra '('
    return partial_result, curr


def pretty_string(nested_list, noindent=False):
    """
    Pretty printer to output lisp-like strings from a nested list of utterances.  
    Specifying 'noindent' will yield a string that is only delimited by spaces, rather than tabs or newlines.  
    :param nested_list: nested list of strings  
    :param noindent: bool  
    :return: string  
    """
    # TODO (medium): Ensure each line does not exceed a certain length.
    result = _pretty_string_aux(nested_list, noindent)
    return result


def _pretty_string_aux(nested_list, noindent, align=0):
    if isinstance(nested_list, str):
        # Single utterance. Just return the string, respecting alignment.
        result = ' ' * align + nested_list
        return result
    # Open parentheses, respecting column alignment
    result = ' ' * align + '('
    operator, *operands = nested_list
    operator_str = operator
    if isinstance(operator, list):
        # Directive or declaration. Switch off indentation for the entire expression.
        noindent = True
        operator_str = _pretty_string_aux(operator, noindent, align)
    # Print operator on the same line and the move to a new line for the operands
    result = result + operator_str + '\n'
    # Print operand strings aligned after the operator
    new_align = align + len(operator_str) + 1
    pretty_operand_strings = [_pretty_string_aux(operand, noindent, new_align) for operand in operands]
    for pretty_operand_string in pretty_operand_strings:
        result = result + pretty_operand_string + '\n'
    # Close parentheses, respecting original alignment
    result = result + ' ' * align + ')'
    # If noindent is true, strip all whitespaces and replace with a single space, respecting alignment.
    if noindent:
        result = ' ' * align + ' '.join(result.split())
    return result


# Additional utilities for denoting a 'lisp-like' string or nested list
def is_lisplike_string(input_str):
    """
    Checking whether a given string is lisp-like.  
    :param input_str: string  
    :return: bool  
    """
    # Parser must be able to parse without raising any exception
    try:
        nested_list_repr = parser(input_str, noerr=False)
        return True
    except Exception:
        return False


def is_lisplike_repr(value):
    """
    Checking whether a value is a string or a nested list of strings.  
    :param value: any  
    :return: bool  
    """
    if isinstance(value, str):
        return True
    if isinstance(value, list):
        return all(is_lisplike_repr(v) for v in value)
    else:
        return False


def is_subexpr_string(subexpr_string, expr_string):
    """
    Check if the first argument is a sub-expression of the second. The expressions are given 
    as strings.  
    :param subexpr_string: string  
    :param expr_string: string  
    :return: bool  
    """
    if not is_lisplike_string(subexpr_string):
        raise ValueError('The arguments need to be a lisp-like string: check first argument.')
    elif not is_lisplike_string(expr_string):
        raise ValueError('The arguments need to be a lisp-like string: check second argument.')
    return subexpr_string in expr_string


def is_subexpr_repr(subexpr_repr, expr_repr):
    """
    Check if the first argument is a sub-expression of the second. The expressions are in the form 
    of the read in representations.  
    :param subexpr_repr: is_lisplike_repr  
    :param expr_repr: is_lisplike_repr  
    :return: bool  
    """
    if not is_lisplike_repr(subexpr_repr):
        raise ValueError('The arguments need to be a lisp-like representation: check first argument.')
    elif not is_lisplike_repr(expr_repr):
        raise ValueError('The arguments need to be a lisp-like representations: check second argument.')
    return is_subexpr_repr_aux(subexpr_repr, expr_repr)


def is_subexpr_repr_aux(subexpr_repr, expr_repr):
    if isinstance(expr_repr, str):
        return subexpr_repr == expr_repr
    elif isinstance(expr_repr, list):
        return subexpr_repr == expr_repr or any(is_subexpr_repr(subexpr_repr, e) for e in expr_repr)
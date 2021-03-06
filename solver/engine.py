"""
Main engine of the minimal SyGuS solver.  
"""

import os
from solver.engine_utils import *


def solve(args):
    """
    Primary function of the engine module. This interprets the arguments and several solver options.  
    """
    infile_full_path = args.infile
    infile_name = os.path.basename(infile_full_path)
    infile_dirname = os.path.dirname(infile_full_path)
    # Create a .tmp folder in the same directory as the input file
    tmp_output_dirname = '.tmp'
    outfile_dirname = os.path.join(infile_dirname, tmp_output_dirname)
    os.makedirs(outfile_dirname, exist_ok=True)
    outfile_name = _get_outfile_name(infile_name)
    outfile_full_path = os.path.join(outfile_dirname, outfile_name)

    sygus_to_smt_options = dict()
    sygus_to_smt_options['additional_constraints'] = []
    solver_call_options = dict()
    solver_call_options['smtsolver'] = args.smtsolver

    # Loop until number of solutions is reached
    # Calculate loop condition based on arguments pertaining to multiple solutions
    solution_number = 1
    while args.stream or (solution_number <= args.num_solutions):
        grammars = sygus_to_smt(infile_full_path, outfile_full_path, sygus_to_smt_options)
        solver_result = call_solver(outfile_full_path, grammars, solver_call_options)
        if solver_result in {'unsat', 'unknown'}:
            print(solver_result)
            exit(0)
        else:
            pretty_solution_string, solution_as_constraint = solver_result
            if not (args.stream or args.num_solutions > 1):
                print('sat')
            print(pretty_solution_string)
            # Append the negation of the solution in order to dismiss it from the next round of synthesis
            sygus_to_smt_options['additional_constraints'].append('(not {})'.format(solution_as_constraint))
        solution_number = solution_number + 1


def _get_outfile_name(infile_name):
    """
    Generate SMT filename based on input filename.  
    :param infile_name: string  
    :return: string  
    """
    dot_index = infile_name.rfind('.')
    outfile_name = '{}.smt2'.format(infile_name[:dot_index])
    return outfile_name

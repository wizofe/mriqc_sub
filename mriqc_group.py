#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mriqc_group.py is a wrapper around mriqc that runs a group-level mriqc job
on the compute cluster.
"""

import os
import subprocess
from pathlib import Path

def main(bidsdir, outputdir='', force=False, mem_gb=1, argstr='', qargstr=''):

    # Defaults
    bidsdir   = Path(bidsdir)
    outputdir = Path(outputdir)
    if not outputdir.name:
        outputdir = bidsdir/'derivatives'/'mriqc'

    # Checks
    if not outputdir.is_dir():
        print(f"ERROR: {outputdir} does not exist")
        return
    reports = list(outputdir.glob('sub-*.html'))
    print(f"\n>>> Found {len(reports)} existing MRIQC-reports in {outputdir}")
    if not reports:
        return

    # Run mriqc
    command = """qsub -l walltime=0:10:00,mem={mem_gb}gb -N mriqc_group {qargs} <<EOF
                 module add mriqc; cd {pwd}
                 {mriqc} {bidsdir} {outputdir} group --nprocs 1 {args}\nEOF"""\
                 .format(pwd       = os.getcwd(),
                         mriqc     = f'unset PYTHONPATH; export PYTHONNOUSERSITE=1; singularity run --cleanenv {os.getenv("DCCN_OPT_DIR")}/mriqc/{os.getenv("MRIQC_VERSION")}/mriqc-{os.getenv("MRIQC_VERSION")}.simg',
                         bidsdir   = bidsdir,
                         outputdir = outputdir,
                         mem_gb    = mem_gb,
                         args      = argstr,
                         qargs     = qargstr)
    running = subprocess.run('if [ ! -z "$(qselect -s RQH)" ]; then qstat -f $(qselect -s RQH) | grep Job_Name | grep mriqc_; fi', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if not force and 'mriqc_' in running.stdout.decode():
        print(f'--> Skipping mriqc_goup because there are still mriqc_sub/group jobs running / scheduled. Use the -f option to override')
    else:
        print(f'--> Submitting job:\n{command}')
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        if process.stderr.decode('utf-8') or process.returncode!=0:
            print(f"ERROR {process.returncode}:\n{process.stderr.decode('utf-8')}\n{process.stdout.decode('utf-8')}")
        else:
            print('\n----------------\n'
                  'Done! Now wait for the job to finish... Check that e.g. with this command:\n\n'
                  '  qstat $(qselect -N mriqc_group)\n\n')


# Shell usage
if __name__ == "__main__":

    # Parse the input arguments and run bidscoiner(args)
    import argparse
    import textwrap

    class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
        pass

    parser = argparse.ArgumentParser(formatter_class=CustomFormatter, description=textwrap.dedent(__doc__),
                                     epilog='for more information see:\n'
                                            '  module help mriqc\n'
                                            '  mriqc -h\n\n'
                                            'examples:\n'
                                            '  mriqc_group.py /project/3022026.01/bids\n'
                                            '  mriqc_group.py /project/3022026.01/bids -o /project/3022026.01/mriqc\n\n'
                                            'Author:\n' 
                                            '  Marcel Zwiers\n ')
    parser.add_argument('bidsdir',          help='The bids-directory with the subject data')
    parser.add_argument('-o','--outputdir', help='The mriqc output-directory where the html-reports are stored (None -> bidsdir/derivatives/mriqc)', default='')
    parser.add_argument('-f','--force',     help='If this flag is given then already running or scheduled mriqc_sub/group jobs with the same name are ignored, otherwise this function-call is cancelled', action='store_false')
    parser.add_argument('-m','--mem_gb',    help='Maximum required amount of memory', default=1, type=int)
    parser.add_argument('-a','--args',      help='Additional arguments that are passed to mriqc (NB: Use quotes and a leading space to prevent unintended argument parsing)', type=str, default='')
    parser.add_argument('-q','--qargs',     help='Additional arguments that are passed to qsub (NB: Use quotes and a leading space to prevent unintended argument parsing)', type=str, default='')
    args = parser.parse_args()

    main(bidsdir=args.bidsdir, outputdir=args.outputdir, force=args.force, mem_gb=args.mem_gb, argstr=args.args)

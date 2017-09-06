# -*- coding: utf-8 -*-
"""
Created on Wed Sep  6 11:27:13 2017

Collecting all the python scripts together in this script.
Make sure that the scripts being called upon is in the same directory!
The common_path may be distinguished from working_dir.

@author: lars
"""

#These directories may then be inputs from a function if that extra step is desired.
working_dir = "/home/lars/playground/real/" 
output_dir = "/home/lars/playground/real/output/" 
input_dir = "/home/lars/playground/sampledata/"

common_path = working_dir

import os

os.chdir(common_path)


print("Starting up the main_flow.py:")
execfile("main_flow.py")
print("Continue with the sub_flow.py:")
execfile("sub_flow.py")
print("Rearrange the SNR/CNR values for diagnostics:")
execfile("compile_snr_cnr.py")


print("Finished..!")
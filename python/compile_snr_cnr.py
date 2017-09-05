# -*- coding: utf-8 -*-
"""
Created on Tue Aug 29 10:33:14 2017

File to append every "snrcnr.txt" to one large matrix/dataframe.

Any large changes to main_flow.py and sub_flow.py may cause this script to not
function as desired.

@author: lars
"""


##Directories which should be equal to the values in main_flow.py and sub_flow.py
working_dir = "/home/lars/playground/real/"
output_dir = "/home/lars/playground/real/output/"
input_dir = "/home/lars/playground/sampledata/"

#Unique for this script
snr_dir = output_dir + "nii/"
import os

x_dummy, dirs, y_dummy = os.walk(input_dir).next()

n = len(dirs)

full_path = output_dir + "super_file.txt"
super_file = open(full_path,"w")

header_string = "id,gm_snr,wm_snr,csf_snr,cnr \n"
super_file.write(header_string)

for x in range(0,n):
    this_id = dirs[x]
    read_path = snr_dir + this_id + "/snrcnr.txt"
    
    this_file = open(read_path,"r")
    
    this_string = this_file.read()
    new_string = this_id + "," + this_string
    
    super_file.write(new_string)
    
    this_file.close()
    

    
super_file.close()
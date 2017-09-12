# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 11:33:19 2017

File to append every "Similar measure" values to a single csv table with a header.

Any large changes to main_flow.py and sub_flow.py may cause this script to not
function as desired.

NMI which is used calculates values above 1, where equal to 1 would indicate no similarity
while values above would indicate similarity, preferably above 1.10


@author: lars
"""

##Directories which should be equal to the values in main_flow.py and sub_flow.py
#working_dir = "/home/lars/playground/real/"
#output_dir = "/home/lars/playground/real/output/"
#input_dir = "/home/lars/playground/sampledata/"

#Unique for this script
similar_dir = output_dir + "nii/"
import os

x_dummy, dirs, y_dummy = os.walk(input_dir).next()

n = len(dirs)

full_path = output_dir + "super_similar_file.txt"
super_file = open(full_path,"w")

header_string = "id,simT1T2 \n"
super_file.write(header_string)

for x in range(0,n):
    this_id = dirs[x]
    read_path = similar_dir + this_id + "/similar_measure.txt"
    
    this_file = open(read_path,"r")
    
    this_string = this_file.read()
    new_string = this_id + "," + this_string
    
    super_file.write(new_string)
    
    this_file.close()
    

super_file.close()
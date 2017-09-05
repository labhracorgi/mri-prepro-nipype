# -*- coding: utf-8 -*-
"""
Created on Mon Aug  7 16:00:38 2017

WorkFlow PreProc Data

Workflow for coregistering and for performing multimodal segmentation.

@author: lars
"""

from nipype import Node, MapNode, Workflow, Function
from nipype import IdentityInterface, DataGrabber, DataSink
from nipype.algorithms.misc import Gunzip
from IPython.display import Image
import os
from nipype.interfaces.spm import Coregister
from nipype.interfaces.base import CommandLine

###Directories - Hardcoded for this purpose.
working_dir = "/home/lars/playground/real/" 
output_dir = "/home/lars/playground/real/output/" 
input_dir = "/home/lars/playground/sampledata/" 

##Recurring directories description:
#Where we want to store the Workflows
#Where we want to sink our data.
#Where our ID/"MRI-images" are.

#SPM directories - Coreg and Segment atlases
atlas_dir = "/home/lars/playground/spm_template/avg152T1.nii"
spm_tpm_dir = "/home/lars/spm12/tpm/TPM.nii"


###Substitutions
substitutions_sink = [('_subject_id_',''),
                      ('_Gunzip','Gunzip'),
                        ('T1_3D_SAG','T1'),
                        ('rT2_FLAIR_3D','FLAIR'),
                        ('rSWI_TRA','SWI')]

####Nodes

##Part 1 - Infosource
infosource = Node(IdentityInterface(fields = ["subject_id","contrasts"]),
                  name="Infosource")

infosource.inputs.contrasts = 1

#Retrieve patient id from folder name
x_dummy, dirs, y_dummy = os.walk(input_dir).next()
subject_list = dirs

#Split into parallel tasks per ID.
infosource.iterables = [('subject_id',subject_list)]


##END Part 1


##Part 2 - DataGrabber
dg = Node(DataGrabber(infields = ["subject_id"],
                      outfields = ["t1w","flair","swi"]),name = "DataGrabber")

dg.inputs.base_directory = input_dir

dg.inputs.template = "*"
dg.inputs.sort_filelist = True

#Should vary depending on the file(s) available
dg.inputs.template_args = {'t1w':[['subject_id']],
                           'flair':[['subject_id']],
                           'swi':[['subject_id']]}
                           
dg.inputs.field_template = {'t1w':'%s/t1w/T1_3D_SAG.nii.gz',
                            'flair':'%s/flair/T2_FLAIR_3D.nii.gz',
                            'swi':'%s/swi/SWI_TRA.nii.gz'}


##END Part 2


##Part 3.0 - GUNZIP - files->list->unzip->list->files
#Files to list
def files_to_list(t1w,flair,swi):
    new_list = [t1w,flair,swi]
    return new_list

dg_to_list_node = Node(Function(input_names=['t1w','flair','swi'],
                                output_names=['gunzip_list'], 
                                function=files_to_list),
                                name='Files_to_List')

#Gunzip
gunzip = MapNode(Gunzip(),name = 'Gunzip',iterfield=['in_file'])

##END Part 3


##Part 4 - SPM CoReg
#
def ready_C1(gunzip_list):
    #Separate list created in "files_to_list"
    t1w = gunzip_list[0]
    flair = gunzip_list[1]
    swi = gunzip_list[2]
    
    #Create new sublist
    sub_list = [flair,swi]
    
    return(t1w,flair,swi,sub_list)

rc1_node = Node(Function(input_names=['gunzip_list'],
                         output_names=['t1w','flair','swi','sub_list'],
                            function=ready_C1),
                            name = 'PreCoregSPM')

coreg_1 = Node(Coregister(),name = 'Coregister_1')
coreg_1.inputs.target = atlas_dir
coreg_1.inputs.cost_function = 'nmi'
coreg_1.inputs.jobtype = 'estimate' #Coreg only

def ready_C1_2(files_coreg_list):
    #Split the list with 2 elements - see "Create new sublist" in ready_C1
    flair_mod = files_coreg_list[0]
    swi_mod = files_coreg_list[1]
    
    return(flair_mod,swi_mod)

rc2_node = Node(Function(input_names=['files_coreg_list'],
                         output_names=['mod_flair','mod_swi'],
                            function=ready_C1_2),
                            name = 'MidCoregSPM')

#Flair
coreg_1a = Node(Coregister(),name = 'Coregister_1a')
coreg_1a.inputs.cost_function = 'nmi'
coreg_1a.inputs.jobtype = 'estwrite' #Coreg and reslice

#Swi
coreg_1b = Node(Coregister(),name = 'Coregister_1b')
coreg_1b.inputs.cost_function = 'nmi'
coreg_1b.inputs.jobtype = 'estwrite' #Coreg and reslice

##END Part 4

##Part 5 - MySegment Multimodal
###Multimodal SPM segment extraction.

def ready_string_to_shell(t1path,t2path):
    
    argument_call = """ "my_mm_spm_segment """ + t1path + " " + t2path + """ /home/lars/spm12/tpm/TPM.nii; exit;" """
    
    ##Look out for formatting issue... Something about representation
    collected_string = argument_call
    return collected_string

ready_string_to_commandline = Node(Function(input_names = ['t1path','t2path'],
                                            output_names = ['collected_string'],
                                            function = ready_string_to_shell),
                                            name = "Collect_T1_T2")
                           
call_to_CL = Node(CommandLine(command = 'matlab -nojvm -nosplash -singleCompThread -r '),name = "Execute_SPM_Through_Shell")

tissue_grab = Node(DataGrabber(),name="GrabTissuesPerSubject")


###END Part 5 -

##Last Part 6 - DataSink
datasink = Node(DataSink(),name = 'Clean_Up_w_DataSink')
datasink.inputs.base_directory = output_dir
datasink.inputs.substitutions = substitutions_sink

##END Last Part 6

####END Nodes


####WorkFlow
#Create it
prepro_flow = Workflow(name = "PreMRI")
prepro_flow.base_dir = working_dir

##Connect nodes.
#InfoSource to Datagrabber
prepro_flow.connect(infosource,'subject_id',dg,'subject_id') 

#DataGrabber files collect in list
prepro_flow.connect([(dg,dg_to_list_node,[('t1w','t1w'),
                                          ('flair','flair'),
                                           ('swi','swi')
                                        ])
                                    ])

#List to Gunzip
prepro_flow.connect(dg_to_list_node,'gunzip_list',gunzip,'in_file')
#prepro_flow.connect(gunzip,'out_file',datasink,'findings')  

#Gunzip to ready_C1
prepro_flow.connect(gunzip,'out_file',rc1_node,'gunzip_list')
                              
#ready_C1 to coreg_1
prepro_flow.connect([(rc1_node,coreg_1,[('t1w','source'),
                                           ('sub_list','apply_to_files')
                                        ])
                                    ])

#coreg_1 to ready_C1_2
prepro_flow.connect(coreg_1,'coregistered_files',rc2_node,'files_coreg_list')

#ready_C1_2 and coreg_1 to coreg_1a
prepro_flow.connect(rc2_node,'mod_flair',coreg_1a,'source')
prepro_flow.connect(coreg_1,'coregistered_source',coreg_1a,'target')

#ready_C1_2 and coreg_1 to coreg_1b
prepro_flow.connect(rc2_node,'mod_swi',coreg_1b,'source')
prepro_flow.connect(coreg_1,'coregistered_source',coreg_1b,'target')

#Coreg_1 to Ready_string
prepro_flow.connect(coreg_1,'coregistered_source',ready_string_to_commandline,'t1path')

#Coreg_1a to Ready_string
prepro_flow.connect(coreg_1a,'coregistered_source',ready_string_to_commandline,'t2path')

#Ready_string to Call_to_CL
prepro_flow.connect(ready_string_to_commandline,'collected_string',call_to_CL,'args')

#To Datasink
prepro_flow.connect(coreg_1,'coregistered_source',datasink,'nii.@t1')
prepro_flow.connect(coreg_1a,'coregistered_source',datasink,'nii.@t2')
prepro_flow.connect(coreg_1b,'coregistered_source',datasink,'nii.@swi')

#Visualize whole WorkFlow.
new_dot =  output_dir + "prepro_flow_graph.dot"
new_dot_png = new_dot + ".png"
prepro_flow.write_graph(graph2use='orig',dotfilename=new_dot)
Image(filename=new_dot_png)

####END WorkFlow
import time

#Run
start = time.time()
res = prepro_flow.run('MultiProc',plugin_args={'n_procs':5})
end = time.time()
print(end - start)
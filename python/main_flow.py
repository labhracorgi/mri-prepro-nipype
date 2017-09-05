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
from nipype.interfaces.spm import Coregister, NewSegment
from nipype.interfaces.fsl.maths import MultiImageMaths, UnaryMaths, ApplyMask
#from nipype.interfaces.ants.segmentation import BrainExtraction #Må ha versjon 0.13.0
from nipype.interfaces.fsl.preprocess import BET
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

##Part 5 - NewSegment
segment = Node(NewSegment(),name='NewSegment_T1')
segment.inputs.channel_info = (0.001, 60, (False, False))

segment.inputs.affine_regularization = 'mni'

segment.inputs.sampling_distance = float(3)
segment.inputs.write_deformation_fields = [False,False]


#tissueX replicates basic matlab script based on running default Segment in SPM12.
tissue1 = ((spm_tpm_dir, int(1)), int(1), (True, False), (False, False))
tissue2 = ((spm_tpm_dir, int(2)), int(1), (True, False), (False, False))
tissue3 = ((spm_tpm_dir, int(3)), int(2), (True, False), (False, False))
tissue4 = ((spm_tpm_dir, int(4)), int(3), (True, False), (False, False))
tissue5 = ((spm_tpm_dir, int(5)), int(4), (True, False), (False, False))
tissue6 = ((spm_tpm_dir, int(6)), int(2), (False, False), (False, False))

segment.inputs.tissues = [tissue1,tissue2,tissue3,tissue4,tissue5,tissue6]
#(('TPM.nii', 1), 2, (True,True), (False, False))


##END Part 5

##Part 6 - Brain Extract

###SPM extraction by segmentation try.
#Extract tissues
def ns_to_extract(new_segment_list):
    
    #Extract and Return Values
    first_tissue = new_segment_list[2][0]
    string_list = [new_segment_list[0][0], new_segment_list[1][0]]#, new_segment_list[3][0]]
    return(first_tissue,string_list)

pre_extract = Node(Function(input_names = ['new_segment_list'],
                            output_names = ['first_tissue','string_list'],
                                function = ns_to_extract),name='PreFSL_TissueExtract')

#Merge Mask
be_fsl = Node(MultiImageMaths(),name='Merge_Tissues_to_Mask')

#This string requires 2 other images in addition to the input
be_fsl.inputs.op_string = "-thr 0.10 -add %s -add %s -thr 0.05 -bin"
#add 1,2,3 "-add %s -add %s -thr 0.01"
#add 2,3 sub 4 "-add %s -add %s -sub %s -thr 0.01"
#add 2 "-add %s -thr 0.01"

#Fill mask

fill_holes = Node(UnaryMaths(),name = 'Fill_Holes_In_Mask')
fill_holes.inputs.operation = 'fillh'

#Apply mask
do_mask_t1 = Node(ApplyMask(),name = 'ApplySegMask_T1')
do_mask_t2 = Node(ApplyMask(),name = 'ApplySegMask_T2')
do_mask_swi = Node(ApplyMask(),name = 'ApplySegMask_SWI')
###END SPM extraction by segmentation try.

###ANTS extraction try. Require 0.13.0 Nipype

#extract_ants = Node(BrainExtraction(),name = "ANTs_BE")

#extract_ants.inputs.dimension = 3
#extract_ants.inputs.brain_template = ants_template_dir + "T_template0.nii.gz"
#extract_ants.inputs.brain_probability_mask = ants_template_dir + "T_template0_BrainCerebellumProbabilityMask.nii.gz"
#extract_ants.inputs.extraction_registration_mask = ants_template_dir + "T_template0_BrainCerebellumExtractionMask.nii.gz"

###END ANTS extraction try

###FSL extraction try.
extract_fsl = Node(BET(),name = "FSL_BE")
#extract_fsl.inputs.remove_eyes = True
extract_fsl.inputs.robust = True
extract_fsl.inputs.mask = True
extract_fsl.inputs.no_output = False

###END FSL extraction try.

##END Part 6

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


###END Multimodal SPM segment extraction.

##Last Part - DataSink
datasink = Node(DataSink(),name = 'Clean_Up_w_DataSink')
datasink.inputs.base_directory = output_dir
datasink.inputs.substitutions = substitutions_sink

##END Last Part

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


#Corrected T1 (from coreg_1) to NewSegment
#prepro_flow.connect(coreg_1,'coregistered_source',segment,'channel_files')

#NewSegment to PreFSL_TissueExtract
#prepro_flow.connect(segment,'native_class_images',pre_extract,'new_segment_list')

#PreFSL_BE to Merge_Tissues_to_Mask
#prepro_flow.connect(pre_extract,'first_tissue',be_fsl,'in_file')
#prepro_flow.connect(pre_extract,'string_list',be_fsl,'operand_files')

#Merge_Tissues_to_Mask to Fill_Holes_In_Mask
#prepro_flow.connect(be_fsl,'out_file',fill_holes,'in_file')

#Fill_Holes_In_Mask to ApplySegMask
#prepro_flow.connect(coreg_1,'coregistered_source',do_mask_t1,'in_file')
#prepro_flow.connect(fill_holes,'out_file',do_mask_t1,'mask_file')


##Needs to be resliced!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#prepro_flow.connect(coreg_1a,'coregistered_source',do_mask_t2,'in_file')
#prepro_flow.connect(fill_holes,'out_file',do_mask_t2,'mask_file')

#prepro_flow.connect(coreg_1b,'coregistered_source',do_mask_swi,'in_file')
#prepro_flow.connect(fill_holes,'out_file',do_mask_swi,'mask_file')

#BrainExtract i ANTS er ikke i nipype 0.11.0
#T1 to ANTS SS
#prepro_flow.connect(coreg_1,'coregistered_source',extract_ants,'anatomical_image')

#T1 to FSL SS
#prepro_flow.connect(coreg_1,'coregistered_source',extract_fsl,'in_file')

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

#Visualize.
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

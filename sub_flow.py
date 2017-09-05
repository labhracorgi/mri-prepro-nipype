# -*- coding: utf-8 -*-
"""
Created on Fri Aug 25 15:54:11 2017

Workflow MidProc data

This workflow is completely dependent on the main_flow.py
If any names are change from main_flow.py, then values must be changed here
too for it to work.

We need this other workflow since a command line (with no output) call was done
to perform the multimodal SPM segmentation algorithm.

Any remaining skullstripping or so should be possible to perform in this 
workflow.

@author: lars
"""

from nipype import Node, Workflow, Function
from nipype import IdentityInterface, DataGrabber, DataSink
import os
from IPython.display import Image
from nipype.interfaces.fsl.maths import MultiImageMaths, UnaryMaths, ApplyMask, Threshold
from nipype.interfaces.ants.segmentation import N4BiasFieldCorrection
from nipype.interfaces.fsl import ImageStats, FAST

##Directories which should be equal to the values in main_flow.py
working_dir = "/home/lars/playground/real/"
output_dir = "/home/lars/playground/real/output/"
input_dir = "/home/lars/playground/sampledata/"


##Start below here:
input_info_dir = input_dir
input_grab_dir = working_dir




substitutions_sink = [('_subject_id_',''),
                      ('_Gunzip','Gunzip'),
                        ('T1_3D_SAG','T1'),
                        ('rT2_FLAIR_3D','FLAIR'),
                        ('rSWI_TRA','SWI'),
                        ('c1T1_3D_SAG_maths_fillh','brain_mask'),                        
                        ('c1','Tissue1'),
                        ('c2','Tissue2'),
                        ('c3','Tissue3'),
                        ('_masked','_mask_stripped')]


#Get subject IDs to be able to extract WF1 MRI and Tissues.
infosource_sub = Node(IdentityInterface(fields = ["subject_id","contrasts"])
                                    ,name = "Infosource_Sub")

infosource_sub.inputs.contrasts = 1

x_dummy, dirs, y_dummy = os.walk(input_info_dir).next()
subject_list = dirs

#Split into parallel tasks per ID.
infosource_sub.iterables = [('subject_id',subject_list)]



#Get WF1 MRI and Tissue files using the ID provided by Infosource

datagrab_sub = Node(DataGrabber(infields = ["subject_id"],
                                outfields = ["t1","flair","swi","c1","c2","c3","c4","c5"]),
                    name = "DataGrabber_Sub")

datagrab_sub.inputs.base_directory = input_grab_dir

datagrab_sub.inputs.template = "*"
datagrab_sub.inputs.sort_filelist = False

#Should vary depending on the file(s) available
datagrab_sub.inputs.template_args = {'t1':[['subject_id']],
                           'flair':[['subject_id']],
                           'swi':[['subject_id']],
                            'c1':[['subject_id']],
                            'c2':[['subject_id']],
                            'c3':[['subject_id']],
                            'c4':[['subject_id']],
                            'c5':[['subject_id']]}
                           
datagrab_sub.inputs.field_template = {'t1':'output/nii/%s/T1.nii',
                            'flair':'output/nii/%s/FLAIR.nii',
                            'swi':'output/nii/%s/SWI.nii',
                            'c1':'PreMRI/_subject_id_%s/Coregister_1/c1T1_3D_SAG.nii',
                            'c2':'PreMRI/_subject_id_%s/Coregister_1/c2T1_3D_SAG.nii',
                            'c3':'PreMRI/_subject_id_%s/Coregister_1/c3T1_3D_SAG.nii',
                            'c4':'PreMRI/_subject_id_%s/Coregister_1/c4T1_3D_SAG.nii',
                            'c5':'PreMRI/_subject_id_%s/Coregister_1/c5T1_3D_SAG.nii'}


##Brain extraction
#Ready the tissues, then merge them together, then fill holes, then apply the mask to the images in output.
def extract_tissue_c123(c1,c2,c3):
    
    #Extract and Return Values
    first_tissue = c1
    string_list = [c2,c3]
    return(first_tissue,string_list)

pre_merge = Node(Function(input_names = ['c1','c2','c3'],
                            output_names = ['first_tissue','string_list'],
                                function = extract_tissue_c123),
                                name = 'Pre_Merge_Tissues')


merge_tissues = Node(MultiImageMaths(),name = "Merge_C1_C2_C3")
merge_tissues.inputs.op_string = "-add %s -add %s -thr 0.05 -bin"

fill_mask = Node(UnaryMaths(),name = "FillHoles_Mask")
fill_mask.inputs.operation = "fillh"

apply_mask_t1 = Node(ApplyMask(),name = "ApplyMask_T1")
apply_mask_flair = Node(ApplyMask(),name = "ApplyMask_FLAIR")
apply_mask_swi = Node(ApplyMask(),name = "ApplyMask_SWI")

#N4 bias field correction.
n4bfc_t1 = Node(N4BiasFieldCorrection(),name = "N4BFC_T1")
n4bfc_t1.inputs.dimension = 3
#n4bfc_t1.inputs.shrink_factor = 4
#n4bfc_t1.inputs.n_iterations = [50,50,50,50]
#n4bfc_t1.inputs.convergence_threshold = 0.001
#n4bfc_t1.inputs.bspline_fitting_distance = 
#n4bfc_t1.inputs.bspline_order = 3
#FAST bias field correction
fast_t1 = Node(FAST(),name = "FASTBFC_T1")
fast_t1.inputs.output_biascorrected = True

###SNR
#Tissue 1-3 mask construction and HeadMask construction.
con_tissue_mask_1 = Node(Threshold(),name = "Tissue1_Mask")
con_tissue_mask_1.inputs.thresh = 0.1
con_tissue_mask_1.inputs.args = "-bin"
con_tissue_mask_2 = Node(Threshold(),name = "Tissue2_Mask")
con_tissue_mask_2.inputs.thresh = 0.1
con_tissue_mask_2.inputs.args = "-bin"
con_tissue_mask_3 = Node(Threshold(),name = "Tissue3_Mask")
con_tissue_mask_3.inputs.thresh = 0.1
con_tissue_mask_3.inputs.args = "-bin"

def extract_tissue_c12345(c1,c2,c3,c4,c5):
    
    first_tissue = c1
    string_list = [c2,c3,c4,c5]
    return(first_tissue,string_list)

ready_12345_tissues = Node(Function(input_names =['c1','c2','c3','c4','c5'],
                                    output_names = ['first_tissue','string_list'],
                                    function = extract_tissue_c12345),
                                    name = "Pre_HeadMask")

con_tissue_mask_head = Node(MultiImageMaths(),name = "HeadMask")
con_tissue_mask_head.inputs.op_string = "-add %s -add %s -add %s -add %s -thr 0.1"

fill_tissue_1 = Node(UnaryMaths(),name = "Fill_Tissue1_Mask")
fill_tissue_1.inputs.operation = "fillh"
fill_tissue_2 = Node(UnaryMaths(),name = "Fill_Tissue2_Mask")
fill_tissue_2.inputs.operation = "fillh"
fill_tissue_3 = Node(UnaryMaths(),name = "Fill_Tissue3_Mask")
fill_tissue_3.inputs.operation = "fillh"

fill_tissue_head = Node(UnaryMaths(),name = "Fill_HeadMask")
fill_tissue_head.inputs.operation = "fillh"

cos_tissue_head = Node(UnaryMaths(),name = "Cos_HeadMask")
cos_tissue_head.inputs.operation = "cos"

thr_tissue_head = Node(Threshold(),name = "Reversed_HeadMask")
thr_tissue_head.inputs.thresh = 0.8 #Must be above cos(1)=~0.54 to properly reverse
thr_tissue_head.inputs.args = "-bin"

#ImageStats - Mean - Std - Length on GM,WM,CSF,BG
mean_image_t1_gm = Node(ImageStats(op_string = "-k %s -M "),name = "Mean_T1_GM")
mean_image_t1_wm = Node(ImageStats(op_string = "-k %s -M "),name = "Mean_T1_WM")
mean_image_t1_csf = Node(ImageStats(op_string = "-k %s -M "),name = "Mean_T1_CSF")
mean_image_t1_bg = Node(ImageStats(op_string = "-k %s -M "),name = "Mean_T1_BG")

std_image_t1_gm = Node(ImageStats(op_string = "-k %s -S "),name = "STD_T1_GM")
std_image_t1_wm = Node(ImageStats(op_string = "-k %s -S "),name = "STD_T1_WM")
std_image_t1_csf = Node(ImageStats(op_string = "-k %s -S "),name = "STD_T1_CSF")
std_image_t1_bg = Node(ImageStats(op_string = "-k %s -S "),name = "STD_T1_BG")

size_image_t1_gm = Node(ImageStats(op_string = "-k %s -V "),name = "Size_T1_GM")
size_image_t1_wm = Node(ImageStats(op_string = "-k %s -V "),name = "Size_T1_WM")
size_image_t1_csf = Node(ImageStats(op_string = "-k %s -V "),name = "Size_T1_CSF")
size_image_t1_bg = Node(ImageStats(op_string = "-k %s -V "),name = "Size_T1_BG")


def merge_snr_info(gm_m,gm_s,gm_l,wm_m,wm_s,wm_l,csf_m,csf_s,csf_l,bg_m,bg_s,bg_l):
    
    #Calculate SNR
    snr_gm = gm_m/bg_s
    snr_wm = wm_m/bg_s
    snr_csf = csf_m/bg_s
    
    #Calculate CNR
    cnr = abs(wm_m-gm_m)/bg_s    
    
    #Have to import since this is an isolated environment.
    import os
    #Specify working dir and names.
    uniq_out_dir = os.getcwd()
    txt_name = "/info.txt"
    full_path = uniq_out_dir + txt_name
    
    #Open the file
    new_file = open(full_path,"w")
    
    #Construct and write the strings.
    string_1 = "Grey matter mean: " + str(gm_m) + " Grey matter std: " + str(gm_s) + " SNR: " + str(snr_gm) + "\n"
    new_file.write(string_1)
    
    string_2 = "White matter mean: " + str(wm_m) + " White matter std: " + str(wm_s) + " SNR: " + str(snr_wm) + "\n"
    new_file.write(string_2)
    
    string_3 = "CSF mean: " + str(csf_m) + " CSF std: " + str(csf_s) + " SNR: " + str(snr_csf) + "\n"
    new_file.write(string_3)    
    
    string_4 = "BG mean: " + str(bg_m) + " BG std: " + str(bg_s) + "\n"
    new_file.write(string_4)
    
    string_5 = "CNR: " + str(cnr) + "\n"
    new_file.write(string_5)
    
    #Close the file.
    new_file.close()
    
    #SNR/CNR only file. [GM,WM,CSF,CNR]
    txt_name_2 = "/snrcnr.txt"    
    full_path_2 = uniq_out_dir + txt_name_2
    new_file_2 = open(full_path_2,"w")
    
    #string_header = "gm,wm,csf,cnr"
    #new_file_2.write(string_header)
    string_final = str(snr_gm) + "," + str(snr_wm) + "," + str(snr_csf) + "," + str(cnr) + "\n"
    new_file_2.write(string_final)
    new_file_2.close()
    
    #Return the path of the directory as proof that the file should be written there.
    #This should probably return the path to the file so that datasink can find it.
    return([full_path,full_path_2])

merge_snr_T1_info_node = Node(Function(input_names = ['gm_m','gm_s','gm_l','wm_m',
                                                   'wm_s','wm_l','csf_m','csf_s',
                                                   'csf_l','bg_m','bg_s','bg_l'],
                                    output_names = ['summary_snr','snr_cnr'],
                                    function = merge_snr_info),
                                    name = "Summarize_SNR")

                                    
                                    
###END SNR

#Datasink.
datasink_sub = Node(DataSink(),name = "DataSink")
datasink_sub.inputs.base_directory = output_dir
datasink_sub.inputs.substitutions = substitutions_sink






#Workflow
midpro_flow = Workflow(name = "MidMRI")
midpro_flow.base_dir = working_dir

midpro_flow.connect(infosource_sub,'subject_id',datagrab_sub,'subject_id')

##WF: Skullstrip
midpro_flow.connect(datagrab_sub,'c1',pre_merge,'c1')
midpro_flow.connect(datagrab_sub,'c2',pre_merge,'c2')
midpro_flow.connect(datagrab_sub,'c3',pre_merge,'c3')

midpro_flow.connect(pre_merge,'first_tissue',merge_tissues,'in_file')
midpro_flow.connect(pre_merge,'string_list',merge_tissues,'operand_files')

midpro_flow.connect(merge_tissues,'out_file',fill_mask,'in_file')


midpro_flow.connect(datagrab_sub,'t1',apply_mask_t1,'in_file')
midpro_flow.connect(fill_mask,'out_file',apply_mask_t1,'mask_file')

midpro_flow.connect(datagrab_sub,'flair',apply_mask_flair,'in_file')
midpro_flow.connect(fill_mask,'out_file',apply_mask_flair,'mask_file')

midpro_flow.connect(datagrab_sub,'swi',apply_mask_swi,'in_file')
midpro_flow.connect(fill_mask,'out_file',apply_mask_swi,'mask_file')
#WF: Skullstrip end

#WF: N4
midpro_flow.connect(apply_mask_t1,'out_file',n4bfc_t1,'input_image')
#midpro_flow.connect(fill_mask,'out_file',n4bfc_t1,'mask_image') 
#Hvordan håndterer n4 i ants 0 verdier?... mtp skullstripped, kanskje man ikke trenger mask da.

#WF: N4 end

#WF: FAST
midpro_flow.connect(apply_mask_t1,'out_file',fast_t1,'in_files')


#WF: FAST end

#WF: SNR
midpro_flow.connect(datagrab_sub,'c1',con_tissue_mask_1,'in_file')
midpro_flow.connect(datagrab_sub,'c2',con_tissue_mask_2,'in_file')
midpro_flow.connect(datagrab_sub,'c3',con_tissue_mask_3,'in_file')

midpro_flow.connect(con_tissue_mask_1,'out_file',fill_tissue_1,'in_file')
midpro_flow.connect(con_tissue_mask_2,'out_file',fill_tissue_2,'in_file')
midpro_flow.connect(con_tissue_mask_3,'out_file',fill_tissue_3,'in_file')


midpro_flow.connect(datagrab_sub,'c1',ready_12345_tissues,'c1')
midpro_flow.connect(datagrab_sub,'c2',ready_12345_tissues,'c2')
midpro_flow.connect(datagrab_sub,'c3',ready_12345_tissues,'c3')
midpro_flow.connect(datagrab_sub,'c4',ready_12345_tissues,'c4')
midpro_flow.connect(datagrab_sub,'c5',ready_12345_tissues,'c5')

midpro_flow.connect(ready_12345_tissues,'first_tissue',con_tissue_mask_head,'in_file')
midpro_flow.connect(ready_12345_tissues,'string_list',con_tissue_mask_head,'operand_files')

midpro_flow.connect(con_tissue_mask_head,'out_file',fill_tissue_head,'in_file')
midpro_flow.connect(fill_tissue_head,'out_file',cos_tissue_head,'in_file')
midpro_flow.connect(cos_tissue_head,'out_file',thr_tissue_head,'in_file')

###Calculating the values
#Mean T1
midpro_flow.connect(datagrab_sub,'t1',mean_image_t1_gm,'in_file')
midpro_flow.connect(fill_tissue_1,'out_file',mean_image_t1_gm,'mask_file')

midpro_flow.connect(datagrab_sub,'t1',mean_image_t1_wm,'in_file')
midpro_flow.connect(fill_tissue_2,'out_file',mean_image_t1_wm,'mask_file')

midpro_flow.connect(datagrab_sub,'t1',mean_image_t1_csf,'in_file')
midpro_flow.connect(fill_tissue_3,'out_file',mean_image_t1_csf,'mask_file')

midpro_flow.connect(datagrab_sub,'t1',mean_image_t1_bg,'in_file')
midpro_flow.connect(thr_tissue_head,'out_file',mean_image_t1_bg,'mask_file')

#Std T1
midpro_flow.connect(datagrab_sub,'t1',std_image_t1_gm,'in_file')
midpro_flow.connect(fill_tissue_1,'out_file',std_image_t1_gm,'mask_file')

midpro_flow.connect(datagrab_sub,'t1',std_image_t1_wm,'in_file')
midpro_flow.connect(fill_tissue_2,'out_file',std_image_t1_wm,'mask_file')

midpro_flow.connect(datagrab_sub,'t1',std_image_t1_csf,'in_file')
midpro_flow.connect(fill_tissue_3,'out_file',std_image_t1_csf,'mask_file')

midpro_flow.connect(datagrab_sub,'t1',std_image_t1_bg,'in_file')
midpro_flow.connect(thr_tissue_head,'out_file',std_image_t1_bg,'mask_file')

#Size T1
midpro_flow.connect(datagrab_sub,'t1',size_image_t1_gm,'in_file')
midpro_flow.connect(fill_tissue_1,'out_file',size_image_t1_gm,'mask_file')

midpro_flow.connect(datagrab_sub,'t1',size_image_t1_wm,'in_file')
midpro_flow.connect(fill_tissue_2,'out_file',size_image_t1_wm,'mask_file')

midpro_flow.connect(datagrab_sub,'t1',size_image_t1_csf,'in_file')
midpro_flow.connect(fill_tissue_3,'out_file',size_image_t1_csf,'mask_file')

midpro_flow.connect(datagrab_sub,'t1',size_image_t1_bg,'in_file')
midpro_flow.connect(thr_tissue_head,'out_file',size_image_t1_bg,'mask_file')

#Providing estimates
midpro_flow.connect(mean_image_t1_gm,'out_stat',merge_snr_T1_info_node,'gm_m')
midpro_flow.connect(mean_image_t1_wm,'out_stat',merge_snr_T1_info_node,'wm_m')
midpro_flow.connect(mean_image_t1_csf,'out_stat',merge_snr_T1_info_node,'csf_m')
midpro_flow.connect(mean_image_t1_bg,'out_stat',merge_snr_T1_info_node,'bg_m')

midpro_flow.connect(std_image_t1_gm,'out_stat',merge_snr_T1_info_node,'gm_s')
midpro_flow.connect(std_image_t1_wm,'out_stat',merge_snr_T1_info_node,'wm_s')
midpro_flow.connect(std_image_t1_csf,'out_stat',merge_snr_T1_info_node,'csf_s')
midpro_flow.connect(std_image_t1_bg,'out_stat',merge_snr_T1_info_node,'bg_s')

midpro_flow.connect(size_image_t1_gm,'out_stat',merge_snr_T1_info_node,'gm_l')
midpro_flow.connect(size_image_t1_wm,'out_stat',merge_snr_T1_info_node,'wm_l')
midpro_flow.connect(size_image_t1_csf,'out_stat',merge_snr_T1_info_node,'csf_l')
midpro_flow.connect(size_image_t1_bg,'out_stat',merge_snr_T1_info_node,'bg_l')
#WF: SNR end

#WF: Datasink
midpro_flow.connect(datagrab_sub,'c1',datasink_sub,'nii.@c1')
midpro_flow.connect(datagrab_sub,'c2',datasink_sub,'nii.@c2')
midpro_flow.connect(datagrab_sub,'c3',datasink_sub,'nii.@c3')

midpro_flow.connect(fill_mask,'out_file',datasink_sub,'nii.@brain_mask')

midpro_flow.connect(apply_mask_t1,'out_file',datasink_sub,'nii.@ss_t1')
midpro_flow.connect(apply_mask_flair,'out_file',datasink_sub,'nii.@ss_flair')
midpro_flow.connect(apply_mask_swi,'out_file',datasink_sub,'nii.@ss_swi')

midpro_flow.connect(n4bfc_t1,'output_image',datasink_sub,'nii.@n4_t1')
midpro_flow.connect(fast_t1,'restored_image',datasink_sub,'nii.@fast_t1')

midpro_flow.connect(merge_snr_T1_info_node,'summary_snr',datasink_sub,'nii.@sum_snr')
midpro_flow.connect(merge_snr_T1_info_node,'snr_cnr',datasink_sub,'nii.@snrcnr')

#WF: Datasink end

#Write the graph:
new_dot =  output_dir + "midpro_flow_graph.dot"
new_dot_png = new_dot + ".png"
midpro_flow.write_graph(graph2use='orig',dotfilename=new_dot)
Image(filename=new_dot_png)


import time
#Run:
start = time.time()
midpro_flow.run('MultiProc',plugin_args={'n_procs':10})
end = time.time()
print(end - start)
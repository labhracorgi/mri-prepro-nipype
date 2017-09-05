## Repository name: "mri-prepro-nipype"
This is a repository for preprocessing MRI images to be used in different types of algorithms for detection stroke, lesions and Circle of Willis.

# Required software:
The following stand-alone software packages have been utilized.
- Nipype:
- SPM:
- FSL:
- ANTS:

or download a collective package.
- NeuroDebian:




# How to run the depository code:

- 1: Set the 3 common directories across all python scripts. (See directory descriptions.)
- 2: Run the "main_flow.py" script for the first level preprocessing.
- 3: Run the "sub_flow.py" script for the second level preprocessing.
- 4: Run the "compile_snr_cnr.py" to extract every SNR and CNR to allow easy diagnostics/check for outliers.




# Current issues:
- Header problems, "sform" is changed somehow ANTS. Possible solution: Copy "qform" and overwrite "sform".


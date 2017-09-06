# Repository name: "mri-prepro-nipype"
This is a repository for preprocessing MRI images to be used in different types of algorithms for detection of stroke, lesions and types of Circle of Willis (CoW).

(This branch is not to be merged to master until the last step of diagnostics are complete!)

### Required software:
The programming languages that have been used (so far) are:
- Python
- Matlab
- R


The following stand-alone neuroimaging software packages have been utilized.
- Nipype: http://nipy.org/packages/nipype/index.html
- SPM: http://www.fil.ion.ucl.ac.uk/spm/software/spm12/
- FSL: https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/
- ANTS: http://stnava.github.io/ANTs/

or download a collective package.
- NeuroDebian: http://neuro.debian.net/




### How to run the repository code:

- 1: Set the 3 common directories across all python scripts. (See directory descriptions in wiki.)
- 2: Run the "main_flow.py" script for the first level preprocessing.
- 3: Run the "sub_flow.py" script for the second level preprocessing.
- 4: Run the "compile_snr_cnr.py" to extract every SNR and CNR value to a single text file which allows easy diagnostics/checking for image outliers.




### Current issues:
- None as of now.



### Wiki:
https://github.com/labhracorgi/mri-prepro-nipype/wiki

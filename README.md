# Repository name: "mri-prepro-nipype"
This is a repository for preprocessing MRI images to be used in different types of algorithms for detection of stroke, lesions and types of Circle of Willis (CoW).

(This branch is not to be merged to master until the last step of diagnostics are complete!)

### Required software:
The programming languages that have been used (so far) are:
- Python (ver. 2.7.9)
- Matlab (ver. 2015b)
- R (ver. 3.3.3)


The following stand-alone neuroimaging software packages have been utilized.
- Nipype: http://nipy.org/packages/nipype/index.html (ver. 0.11.0)
- SPM: http://www.fil.ion.ucl.ac.uk/spm/software/spm12/ (ver. 12)
- FSL: https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/ (ver. 5.0)

or download a collective package.
- NeuroDebian: http://neuro.debian.net/




### How to run the repository code:
With "super_flow.py":
- 1: Set the 3 necessary and common directories (working, input and output) in "super_flow.py".
- 2: Place every script in the working directory.
- 3: Run "super_flow.py".

Without "super_flow.py":
- 1: Set the 3 common directories across all python scripts. (See directory descriptions in wiki.)
- 2: Run the "main_flow.py" script for the first level preprocessing.
- 3: Run the "sub_flow.py" script for the second level preprocessing.
- 4: Run the "compile_snr_cnr.py" to extract every SNR and CNR value to a single text file which allows easy diagnostics/checking for image outliers.
- 5: Run the "compile_similar_values.py" to extract every "nmi"-based similarity measure between T1 and T2 image.

### Current issues:
- None as of now.

### Possible issues:
- Lack of options conditions to handle errors. Especially in calls to external Matlab scripts!

### Wiki:
https://github.com/labhracorgi/mri-prepro-nipype/wiki

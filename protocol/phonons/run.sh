#!/bin/bash
# input: 
# $1 job_name
# $2 input_file.json
# $3 output_file.json
# $4 plot.nbconvert.ipynb
# 
# output: 
# output.json
# plot.nbconvert.ipynb

# conda env create --name $1 --file=${script_dir}/environments.yml
# conda activate $1 
papermill ${script_dir}/script.ipynb -k 'python3' -p input_file $2 -p output_file $3
papermill ${script_dir}/plot.ipynb $4 -k 'python3' -p input_file $3
# conda deactivate
# conda remove --name $1 --all

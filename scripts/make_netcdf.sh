#!/bin/bash

#
# ./make_netcdf.sh YYYYmmdd
#

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

#gws_path=/gws/pw/j07/ncas_obs_vol1

#netcdf_path=${gws_path}/iao/processing/ncas-ceilometer-3/netcdf_files
#datapath=${gws_path}/iao/raw_data/ncas-ceilometer-3/incoming
#logfilepath=${gws_path}/iao/logs/ncas-ceilometer-3

netcdf_path=/home/earjham/netcdf/ncas-sunphotometer-3
datapath=/data/ncas-sunphotometer-3
logfilepath=/home/earjham/logs/ncas-sunphotometer-3

metadata_file=${SCRIPT_DIR}/../metadata.csv


datadate=$1  # YYYYmmdd
conda_env=${2:-netcdf}
conda_path=${3:-/home/earjham/miniforge3/envs}

year=${datadate:0:4}
month=${datadate:4:2}
day=${datadate:6:2}

${conda_path}/${conda_env}/bin/python ${SCRIPT_DIR}/../process_sunphotometer.py ${datapath}/${year}-${month}-${day}_SSIM_Data_SN155.csv -m ${metadata_file} -o ${netcdf_path} -v -t /home/earjham/bin/AMF_CVs-2.0.0/product-definitions/tsv


if [ -f ${netcdf_path}/ncas-sunphotometer-3_iao_${datadate}_aerosol-optical-depth_*.nc ]
then 
  file_exists=True
else
  file_exists=False
fi


cat << EOF | sed -e 's/#.*//; s/  *$//' > ${logfilepath}/${datadate}.txt
Date: $(date -u)
aerosol-optical-depth file created: ${file_exists}
EOF

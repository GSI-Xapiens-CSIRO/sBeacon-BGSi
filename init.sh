#!/usr/bin/bash
# argument optional, will be passed into add_compile_options()
# e.g ./init.sh '-march=ivybridge'

# 
# Housekeeping and cleanups
# 

set -ex
REPOSITORY_DIRECTORY="${PWD}"
LIBRARIES="${REPOSITORY_DIRECTORY}/libraries"
SOURCE="${LIBRARIES}/source"

# Clean sbeacon-libraries
if [ -d "${LIBRARIES}" ]
  then
    rm -rf "${LIBRARIES}"
fi

mkdir "${LIBRARIES}"
mkdir "${SOURCE}"

#
# building lambda layers
#

# tabix
cd ${SOURCE}
git clone --recursive --depth 1 --branch develop https://github.com/samtools/htslib.git 
cd htslib && autoreconf && ./configure --enable-libcurl && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
# TODO check what libraries are missing and add only those
ldd ${SOURCE}/htslib/tabix | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/htslib/tabix ./layers/binaries/bin/
ldd ${SOURCE}/htslib/htsfile | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/htslib/htsfile ./layers/binaries/bin/

# bcftools
cd ${SOURCE}
git clone --recursive --depth 1 --branch develop https://github.com/samtools/bcftools.git
cd bcftools && autoreconf && ./configure && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
ldd ${SOURCE}/bcftools/bcftools | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/bcftools/bcftools ./layers/binaries/bin/

# samtools
cd ${SOURCE}
git clone --recursive --depth 1 --branch develop https://github.com/samtools/samtools.git
cd samtools && autoreconf && ./configure --without-curses && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
ldd ${SOURCE}/samtools/samtools | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/samtools/samtools ./layers/binaries/bin/

# libmagic 
cd ${SOURCE}
git clone --depth 1 https://github.com/file/file.git
cd file && autoreconf -i && ./configure && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
cp ${SOURCE}/file/src/.libs/libmagic.so.1 ./layers/binaries/lib/

# python libraries layer
cd ${REPOSITORY_DIRECTORY}
pip install ijson==3.3.0 --target layers/python_libraries/python
pip install jsons==1.6.3 --target layers/python_libraries/python
pip install jsonschema==4.18.0 --target layers/python_libraries/python
pip install markupsafe==2.0.1 --target layers/python_libraries/python
pip install pydantic==2.0.2 --target layers/python_libraries/python
pip install pyhumps==3.8.0 --target layers/python_libraries/python
pip install pynamodb==6.0.0 --target layers/python_libraries/python
pip install pyorc==0.9.0 --target layers/python_libraries/python
pip install requests==2.31.0 --target layers/python_libraries/python
pip install smart_open==7.0.4 --target layers/python_libraries/python
pip install strenum==0.4.15 --target layers/python_libraries/python
pip install python-magic==0.4.27 --target layers/python_libraries/python
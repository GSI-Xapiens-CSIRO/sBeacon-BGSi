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
wget https://github.com/samtools/htslib/releases/download/1.21/htslib-1.21.tar.bz2
tar -xf htslib-1.21.tar.bz2
cd htslib-1.21 && autoreconf && ./configure --enable-libcurl && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
# TODO check what libraries are missing and add only those
ldd ${SOURCE}/htslib-1.21/tabix | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/htslib-1.21/tabix ./layers/binaries/bin/
ldd ${SOURCE}/htslib-1.21/htsfile | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/htslib-1.21/htsfile ./layers/binaries/bin/

# bcftools
cd ${SOURCE}
wget https://github.com/samtools/bcftools/releases/download/1.21/bcftools-1.21.tar.bz2
tar -xf bcftools-1.21.tar.bz2
cd bcftools-1.21 && autoreconf && ./configure && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
ldd ${SOURCE}/bcftools-1.21/bcftools | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/bcftools-1.21/bcftools ./layers/binaries/bin/

# samtools
cd ${SOURCE}
wget https://github.com/samtools/samtools/releases/download/1.21/samtools-1.21.tar.bz2
tar -xf samtools-1.21.tar.bz2
cd samtools-1.21 && autoreconf && ./configure --without-curses && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
ldd ${SOURCE}/samtools-1.21/samtools | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/samtools-1.21/samtools ./layers/binaries/bin/

# libmagic 
cd ${SOURCE}
wget https://github.com/file/file/archive/refs/tags/FILE5_46.tar.gz
tar -xf FILE5_46.tar.gz
cd file-FILE5_46 && autoreconf -i && ./configure && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
cp ${SOURCE}/file-FILE5_46/src/.libs/libmagic.so.1 ./layers/binaries/lib/

# Clean up the python layers directory
if [ -d "${REPOSITORY_DIRECTORY}/layers/python_libraries/python" ]
  then
    rm -rf "${REPOSITORY_DIRECTORY}/layers/python_libraries/python"
fi
mkdir -p "${REPOSITORY_DIRECTORY}/layers/python_libraries/python"

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
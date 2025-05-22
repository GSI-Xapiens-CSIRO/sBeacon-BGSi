#!/usr/bin/bash
# argument optional, will be passed into add_compile_options()
# e.g ./init.sh '-march=ivybridge'

#
# Housekeeping and cleanups
#

if command -v pip3 >/dev/null 2>&1; then
    PIP_CMD=pip3
elif command -v pip >/dev/null 2>&1; then
    PIP_CMD=pip
elif [ -x "/usr/bin/pip3" ]; then
    PIP_CMD=/usr/bin/pip3
elif [ -x "/usr/bin/pip" ]; then
    PIP_CMD=/usr/bin/pip
elif [ -x "/usr/local/bin/pip3" ]; then
    PIP_CMD=/usr/local/bin/pip3
elif [ -x "/usr/local/bin/pip" ]; then
    PIP_CMD=/usr/local/bin/pip
else
    echo "Error: pip not found"
    exit 1
fi

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

# python libraries layer
cd ${REPOSITORY_DIRECTORY}
$PIP_CMD install ijson==3.3.0 --target layers/python_libraries/python
$PIP_CMD install jsons==1.6.3 --target layers/python_libraries/python
$PIP_CMD install jsonschema==4.18.0 --target layers/python_libraries/python
$PIP_CMD install markupsafe==2.0.1 --target layers/python_libraries/python
$PIP_CMD install pydantic==2.0.2 --target layers/python_libraries/python
$PIP_CMD install pyhumps==3.8.0 --target layers/python_libraries/python
$PIP_CMD install pynamodb==6.0.0 --target layers/python_libraries/python
$PIP_CMD install pyorc==0.9.0 --target layers/python_libraries/python
$PIP_CMD install requests==2.31.0 --target layers/python_libraries/python
$PIP_CMD install smart_open==7.0.4 --target layers/python_libraries/python
$PIP_CMD install strenum==0.4.15 --target layers/python_libraries/python
$PIP_CMD install python-magic==0.4.27 --target layers/python_libraries/python
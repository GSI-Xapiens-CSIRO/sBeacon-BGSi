FROM public.ecr.aws/lambda/python:3.12-x86_64

RUN dnf update -y && dnf install -y \
    git \
    gcc \
    gcc-c++ \
    make \
    autoconf \
    automake \
    zlib-devel \
    bzip2-devel \
    xz-devel \
    libcurl-devel \
    openssl-devel

WORKDIR /src

RUN git clone --recursive --depth 1 --branch develop https://github.com/samtools/htslib.git \
    && cd htslib \
    && autoreconf --install \
    && ./configure \
    && make \
    && make install

RUN git clone --recursive --depth 1 --branch develop https://github.com/samtools/bcftools.git \
    && cd bcftools \
    && autoreconf --install \
    && ./configure \
    && make \
    && make install
    
RUN mkdir -p /opt/bin
RUN mkdir -p /opt/lib

RUN cp $(command -v tabix) /opt/bin
RUN ldd $(command -v tabix) | awk 'NF == 4 { system("cp " $3 " /opt/lib") }'

RUN cp $(command -v bcftools) /opt/bin
RUN ldd $(command -v bcftools) | awk 'NF == 4 { system("cp " $3 " /opt/lib") }'

WORKDIR ${LAMBDA_TASK_ROOT}/

ENV LD_LIBRARY_PATH="/opt/lib:$LD_LIBRARY_PATH"

COPY requirements.txt ${LAMBDA_TASK_ROOT}/

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY *.py ${LAMBDA_TASK_ROOT}/

COPY schemas ${LAMBDA_TASK_ROOT}/schemas

ADD shared ${LAMBDA_TASK_ROOT}/shared

CMD ["lambda_function.lambda_handler"]
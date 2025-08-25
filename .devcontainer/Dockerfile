FROM --platform=x86_64 public.ecr.aws/sam/build-python3.12:latest-x86_64

RUN dnf update -y
RUN dnf install -y git tar make openssl-devel libcurl-devel wget bzip2-devel xz-devel libffi-devel zlib-devel autoconf intltool 
RUN dnf install -y gcc gcc-c++ cmake
RUN dnf install -y docker

RUN wget https://releases.hashicorp.com/terraform/1.12.2/terraform_1.12.2_linux_amd64.zip
RUN unzip terraform_1.12.2_linux_amd64.zip -d /usr/bin/

# Copy requirements.txt
RUN pip install --upgrade pip
COPY requirements.txt ./
RUN pip install -r requirements.txt

# pnpm
RUN wget -qO- https://get.pnpm.io/install.sh | ENV="$HOME/.bashrc" SHELL="$(which bash)" bash -
# nodejs
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
RUN source $HOME/.bashrc && nvm install 20

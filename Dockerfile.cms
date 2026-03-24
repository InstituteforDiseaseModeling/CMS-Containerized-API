FROM rockylinux:9.2

LABEL version="1.0.0"
LABEL description="Rocky Linux based container for running IDM's compartmental modeling software (CMS)"

RUN yum update -y

# mono .Net runtime
RUN update-crypto-policies --set DEFAULT:SHA1
RUN rpmkeys --import "http://keyserver.ubuntu.com/pks/lookup?op=get&search=0x3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF"
RUN curl https://download.mono-project.com/repo/centos8-stable.repo | tee /etc/yum.repos.d/mono-centos8-stable.repo
RUN dnf install -y mono-complete

# python.net
RUN yum install -y clang python3-pip
RUN python3 -m pip install pythonnet==3.0.3 numpy==1.26.2 matplotlib==3.8.1 pandas==2.1.3

# This causes pythonnet to include /cms in the list of folders it looks in for assemblies.
ENV PYTHONPATH=/cms

COPY bin /cms
COPY models/seir.py /cms
COPY cmsmodel.py /cms

CMD python3 /cms/seir.py --png

ARG VERSION=latest
ARG CAPI_USER=None
ARG CAPI_PASSWORD=None
ARG JFROG_DOWNLOAD_TOKEN

FROM amr-registry-pre.caas.intel.com/vce-devops/avocado_base_image:${VERSION}
# LABEL about the custom image
LABEL maintainer="juan.wolf.maqueda@intel.com"
LABEL version="1.1"
LABEL description="Avocado environment for VCE ABAF test content"

RUN mkdir /root/drivers.io.vmware.validation.capi-automation
COPY . /root/drivers.io.vmware.validation.capi-automation

ENV http_proxy "http://proxy-chain.intel.com:911/"
ENV https_proxy "http://proxy-chain.intel.com:912/"

RUN apt-get update && apt-get -y install sudo
RUN sudo apt-get install python3-venv -y \
    && sudo apt-get install python3-tz -y \ 
    && sudo apt-get install tzdata

#RUN echo ${JFROG_DOWNLOAD_TOKEN}
#RUN echo "${JFROG_DOWNLOAD_TOKEN}"

CMD cd /root \
    && curl -H "X-JFrog-Art-Api:$JFROG_DOWNLOAD_TOKEN" -O "https://ubit-artifactory-or.intel.com/artifactory/vce-devops-storage-or-local/tcf-workstation-setup.sh" \
    && chmod a+x tcf-workstation-setup.sh \
    && ./tcf-workstation-setup.sh \
    && source /root/.bashrc \
    && tcf.git/tcf login ${secrets.CAPI_USER} -p '$CAPI_PASSWORD' \

RUN tcf ls -v
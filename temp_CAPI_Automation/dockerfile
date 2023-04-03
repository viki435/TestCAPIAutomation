FROM devops.vce.docker.registry:5000/sys_vceops/avocado_base:v1.3.0
RUN wget https://plen-ci.ostc.intel.com/job/TCF-master/lastSuccessfulBuild/artifact/tcf-workstation-setup.sh --no-check-certificate
RUN chmod a+x tcf-workstation-setup.sh
RUN ./tcf-workstation-setup.sh
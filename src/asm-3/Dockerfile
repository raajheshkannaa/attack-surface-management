FROM public.ecr.aws/lambda/python:3.9

RUN yum install -y nmap which sudo

# Copy function code
COPY asm-3.py ${LAMBDA_TASK_ROOT}

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "asm-3.main" ]
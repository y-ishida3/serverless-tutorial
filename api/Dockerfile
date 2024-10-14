FROM public.ecr.aws/lambda/python:3.10

WORKDIR ${LAMBDA_TASK_ROOT}/api

COPY ./requirements.txt handler.py ./
COPY ./src/ ./src

RUN pip install --upgrade pip &&\
    pip install -r requirements.txt
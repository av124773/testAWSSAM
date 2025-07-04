FROM public.ecr.aws/lambda/python:3.10

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.3 \
     /lambda-adapter /opt/extensions/lambda-adapter

# 讓 Web Adapter 用串流模式
ENV AWS_LWA_INVOKE_MODE=response_stream  

# Uvicorn 監聽的埠
ENV PORT=8000                             

WORKDIR ${LAMBDA_TASK_ROOT}

COPY layers/common_utils/dist/common_utils-0.1.0-py3-none-any.whl .
RUN pip install common_utils-0.1.0-py3-none-any.whl

COPY function/streaming_message/requirements.txt ./
RUN pip install -r requirements.txt

COPY function/streaming_message/stream_api.py ./

ENTRYPOINT ["uvicorn", "stream_api:app", "--host", "0.0.0.0", "--port", "8000"]

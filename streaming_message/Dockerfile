FROM public.ecr.aws/lambda/python:3.10

# COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.3 /lambda-adapter /opt/extensions/lambda-adapter
# 下載並安裝官方 RIC extension

# RUN mkdir -p /opt/extensions \
#  && curl -Lo /opt/extensions/aws-lambda-ric \
#       https://github.com/aws/aws-lambda-runtime-interface-client/releases/latest/download/aws-lambda-ric \
#  && chmod +x /opt/extensions/aws-lambda-ric

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.3 \
     /lambda-adapter /opt/extensions/lambda-adapter
# 讓 Web Adapter 用串流模式
ENV AWS_LWA_INVOKE_MODE=response_stream  
# Uvicorn 監聽的埠
ENV PORT=8000                             

WORKDIR ${LAMBDA_TASK_ROOT}

# 將共用程式碼目錄複製到映像中
COPY layers/common_utils/common_utils ./common

COPY streaming_message/requirements.txt ./
RUN pip install -r requirements.txt

COPY streaming_message/stream_api.py ./

ENTRYPOINT ["uvicorn", "stream_api:app", "--host", "0.0.0.0", "--port", "8000"]

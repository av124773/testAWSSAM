FROM public.ecr.aws/lambda/python:3.10

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.3 \
     /lambda-adapter /opt/extensions/lambda-adapter
 
# Uvicorn 監聽的埠
ENV PORT=8000                             

WORKDIR ${LAMBDA_TASK_ROOT}

# 將共用程式碼目錄複製到映像中
COPY layers/common_utils/common ./common

COPY hello_world/requirements.txt ./
RUN pip install -r requirements.txt

COPY hello_world/hello_api.py ./

ENTRYPOINT ["uvicorn", "hello_api:app", "--host", "0.0.0.0", "--port", "8000"]

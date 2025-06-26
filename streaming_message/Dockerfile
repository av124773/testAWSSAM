FROM public.ecr.aws/lambda/python:3.10

# COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.3 /lambda-adapter /opt/extensions/lambda-adapter
# 下載並安裝官方 RIC extension
RUN mkdir -p /opt/extensions \
 && curl -Lo /opt/extensions/aws-lambda-ric \
      https://github.com/aws/aws-lambda-runtime-interface-client/releases/latest/download/aws-lambda-ric \
 && chmod +x /opt/extensions/aws-lambda-ric

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app.py ./

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

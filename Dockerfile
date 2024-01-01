FROM python:3.10
MAINTAINER label="Rohan"
WORKDIR /app
COPY . /app
# Optional to include your kube config in docker container.
COPY /path/to/your/kube-config /root/.kube/config 
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "manual_alert.py"]
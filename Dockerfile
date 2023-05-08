FROM python
WORKDIR /app
EXPOSE 55352
RUN pip install --upgrade pip
COPY . /app
CMD ["python3", "server2.py", "0.0.0.0", "55352"]

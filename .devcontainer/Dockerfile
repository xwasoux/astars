FROM python:3.12

ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt -y update && apt -y upgrade
RUN apt -y install \
	build-essential \
	python3-pip \
	python3-wheel \
	vim \
	git \
	tig \
	tmux \
	tree \
	graphviz

RUN pip install --upgrade pip

COPY requirements-dev.txt .
COPY . /app
WORKDIR /app

RUN pip install -r requirements-dev.txt

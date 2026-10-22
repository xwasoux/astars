FROM python:3.12

ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt -y update && apt -y upgrade
RUN apt -y install \
	build-essential \
	curl \
	python3-pip \
	python3-wheel \
	vim \
	git \
	tig \
	tmux \
	tree \
	graphviz

# Rust toolchain: crates/astars-core, bindings/python (pyo3), bindings/node (napi-rs)
ENV RUSTUP_HOME=/usr/local/rustup \
	CARGO_HOME=/usr/local/cargo \
	PATH=/usr/local/cargo/bin:$PATH
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path --default-toolchain stable

# Node.js: bindings/node
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
	&& apt -y install nodejs

RUN pip install --upgrade pip

COPY requirements-dev.txt .
COPY . /app
WORKDIR /app

RUN pip install -r requirements-dev.txt

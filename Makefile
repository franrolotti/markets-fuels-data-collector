.PHONY: setup fetch export validate docker


PY=python
PKG=mf
OUT=fuels_daily.parquet


setup:
$(PY) -m pip install --upgrade pip
$(PY) -m pip install -e .


fetch:
$(PY) -m $(PKG) fetch --start 2018-01-01 --end 2025-12-31 --series brent stoxx ibex cac psi20


export:
mkdir -p export
cp $(OUT) export/$(OUT)


validate:
$(PY) -m $(PKG) validate --dataset fuels_daily


# basic docker build/run examples


docker:
docker build -t markets-fuels:latest .
docker run --rm -v "$$(pwd)":/app markets-fuels:latest make fetch
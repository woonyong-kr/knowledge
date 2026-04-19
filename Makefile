PYTHON ?= python3

.PHONY: help scaffold validate build clean rebuild all

help:
	@echo "사용 가능한 명령:"
	@echo "  make scaffold  - tree.yaml 기준으로 docs/ 폴더·README 생성/갱신"
	@echo "  make validate  - tree.yaml 과 docs/ 구조의 정합성 검사"
	@echo "  make build     - post/ 디렉터리 미러 빌드 (기존 post/ 삭제 후 재생성)"
	@echo "  make clean     - post/ 디렉터리 삭제"
	@echo "  make rebuild   - clean + build"
	@echo "  make all       - validate + scaffold + build"

scaffold:
	$(PYTHON) scripts/scaffold.py

validate:
	$(PYTHON) scripts/validate.py

build:
	$(PYTHON) scripts/build_posts.py

clean:
	rm -rf post

rebuild: clean build

all: validate scaffold build

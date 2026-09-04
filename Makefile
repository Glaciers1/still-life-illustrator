.PHONY: test lint format check-deps doctor dry-run install install-dev release

# 运行单元测试
test:
	python -m pytest tests/ -v

# 代码风格检查
lint:
	python -m flake8 scripts/ --config=.flake8

# 代码格式化（需要安装 black）
format:
	python -m black scripts/ --line-length 120

# 检查依赖
check-deps:
	python -c "import PIL; print(f'Pillow {PIL.__version__}')"
	python -c "import urllib.request; print('urllib OK (standard library)')"
	@echo "依赖检查完成"

# 运行技能自诊断
doctor:
	python scripts/skill_doctor.py

# dry-run 批量校验（示例）
dry-run:
	python scripts/build_from_brief.py --batch $(BATCH_DIR) --dry-run

# 安装依赖
install:
	pip install -r requirements.txt

# 安装开发依赖（测试+lint+格式化）
install-dev:
	pip install -r requirements.txt
	pip install pytest flake8 black

# 发布新版本：提交 + 打 tag + 推送（用法: make release VERSION=3.1.0）
release:
	git add .
	git commit -m "release v$(VERSION)"
	git tag v$(VERSION)
	git push origin main
	git push origin v$(VERSION)
	@echo "已发布 v$(VERSION)"

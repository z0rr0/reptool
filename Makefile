NAME=reptool
HOST=127.0.0.1
PORT=8001
ADDR=reptool.org
MANAGE=web/manage.py
PID=/tmp/.$(NAME).pid

all: test

test:
	uv run $(MANAGE) test team

start:
	@echo "  >  $(NAME)"
	uv run $(MANAGE) runserver --noreload $(HOST):$(PORT) & echo $$! > $(PID)
	@-cat $(PID)
	@echo "  >  http://$(ADDR):$(PORT)"

stop:
	@-touch $(PID)
	@-cat $(PID)
	@-kill `cat $(PID)` || true
	@-rm $(PID)

restart: stop start

default: 
	python3 pft_detect_threats_and_email.py

fmt:
	black . $(ARGS)

install:
	pip3 install --user -r requirements.txt

lint:
	pylint pft_detect_threats_and_email.py

.PHONY: \
	fmt \
	install	\
	lint
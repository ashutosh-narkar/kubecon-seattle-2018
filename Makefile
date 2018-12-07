.PHONY: images-prod
images-prod:
	@./src/build-services-prod.sh

.PHONY: images-dev
images-dev:
	@./src/build-services-dev.sh

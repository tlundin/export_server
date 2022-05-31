app_name = flask-prod-app

build:
	docker build -t $(app_name) .

run:
	docker run --name $(app_name) \
		--detach -p 8003:8003 $(app_name) \
		-v /home/ubuntu/files:/files \
		-v /home/ubuntu/images:/images

kill:
	docker stop $(app_name)
	docker container prune -f
	docker rmi -f $(app_name)


all:
	@docker-compose up -d

clean:
	@docker-compose down

fclean:
	@docker-compose down --rmi all --volumes

re:
	@docker-compose up -d --build

.PHONY: all clean fclean re

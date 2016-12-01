PORT = 8888
FILE = cities.txt

SearchServerMain.jar:
	ant jar

start: SearchServerMain.jar
	java -jar SearchServerMain.jar $(FILE) $(PORT)

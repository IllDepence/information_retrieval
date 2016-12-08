PORT = 8888
FILE = cities2.txt

SearchServerMain.jar:
	ant jar

start: SearchServerMain.jar
	java -jar SearchServerMain.jar $(FILE) $(PORT)

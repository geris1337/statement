# Statement task

These files are intended to run on Debian based systems.

### Prerequisites

These can be installed by launching the prepare.sh script
```
git https://github.com/geris1337/statement.git
cd statement
sudo sh prepare.sh
```
**Don't forget to place *docker-compose.yml* file inside the project directory !!!**

Once file is present, run the following to start up the containers
```
sudo docker-compose up -d
```

## Finally, run the test

Execute the following line
```
pytest -v
```

or
```
python3 -m pytest -v
```

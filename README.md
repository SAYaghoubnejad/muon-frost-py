# Muon Frost
     
### Setup the environment
To run the project, first run 5 terminals for 4 nodes and 1 gateway. 

Create a new venv and activate it for every terminal. Next, install the required packages by running this command:

    $(venv) pip install -r requirements.txt

After installtion, clone the python libp2p package and install it manually for the venv.


Change the directoy to the muon_frost root project and run the following command for every terminal to configure the root path of the python project:

    $(venv) $PYTHONPATH:./ 


### Run the project
Run the nodes first. Type the following command in 4 terminals to intitiate them:

    $(venv) python node/main.py [1-4]

For the last step run the gateway in the last terminal:
    
    $(venv) python gateway/main.py

# Muon FROST
This is the Python implementation of FROST algorithem for the Muon network.
     
## How to Setup

To create a `venv` and install the required packages, you can run the following commands:
    
    $ git clone https://github.com/SAYaghoubnejad/muon-frost-py.git --recurse-submodules
    $ cd muon-frost-py
    $ virtualenv -p python venv
    $ . venv/bin/activate
    $(venv) pip install -r requirements.txt

Note that the rquired python version is `python3.10`.

## How to Run

To run the project first run `m` additional terminals for `m` nodes and activate the `venv` on these terminals. Note that `m` is an arbitrary positive nummber. Then change the directoy to the `muon-frost-py` root project and run the following command for every terminal to configure the root path of the python project:

    $(venv) export PYTHONPATH="./:$PYTHONPATH"

Run the nodes first. Type the following command in `m` terminals to intitiate them:

    $(venv) python node/main.py [0-n]

For the last step run the gateway in the last terminal:
    
    $(venv) python gateway/main.py [number of nodes you ran] [treshold] [n] [number of signature]

Gateway take 4 parameters as input:
1. The `number of nodes you ran` 
2. The `treshold` of FROST algorithem which is an integer ($t \leq n$)
3. The `n` is the nodes number that cooperates with gateway to generate a distributed key ($n \leq m$)
4. `number of signature` is the number of signature requested by gateway upon completion of DKG

# Monitor nodes 

Simple implementation nodes monitor using Apache Zookeeper Server



## Commands:


    Python3(main.py):
        
print("")
    print(" Monitor Servers:\n")
    print("     - ServerInstall     hostname userName password")
    print("     - ServerStart")
    print("     - ServerUninstall")
    print("     - ServerStop \n")
    print(" Nodes clients:\n")
    print("     - ClientInstall     hostname userName password")
    print("     - ClientAdd         hostname userName password")
    print("     - ClientRemove      hostname userName password\n")
    print(" Monitor:\n")
    print("     - AllState")
    print("     - ClientState       hostname userName password")
    print("     - MonitorSettings    \n\n")
    print("")

    Monitor Servers:                            Parameters

        ServerInstall                |   hostname userName password
        ServerStart                  |              -
        ServerUninstall              |   
        ServerStop                   |   

    Nodes clients:

        ClientInstall                |   hostname userName password
        ClientAdd                    |   hostname userName password
        ClientRemove                 |   hostname userName password
    
    Monitor:

        AllState                     |              -
        ClientState                  |   hostname userName password
        MonitorSettings              |              -

    --------------------------------------------------------------
   
    Arguments(main.py):

        -h, --help                |   Show this help message and exit
        --original_swarm_file     |   File of ground truth.
        --training_swarm_file     |   File of training samples
        --corrected_swarm_file    |   File of correction
        --validation_swarm_file   |   File of validation
        --failed_swarm_file       |   File of failed swarm
        --analyse_file            |   Analyse results with statistics
        --dense_layers            |   Number of dense layers (e.g. 1, 2, 3)
        --neurons                 |   Number neurons per layer
        --cells                   |   Numbers cells(neurons) LSTM
        --num_sample_training     |   Number samples for training
        --num_epochs              |   Number epochs training
        --analyse_file_mode       |   Open mode (e.g. 'w' or 'a')
        --model_architecture_file |   Full model architecture file
        --model_weights_file      |   Full model weights file
        --size_window_left        |   Left window size
        --size_window_right       |   Right window size
        --threshold               |   i.e. alpha (e.g. 0.5 - 0.95)
        --pif PIF                 |   Pif (only for statistics)
        --dataset                 |   Dataset (only for statistics)
        --seed                    |   Seed (only for statistics)
        --lstm_mode               |   Activate LSTM mode
        --skip_train, -t          |   Skip training of the machine learning model
        --skip_correct, -c        |   Skip correction of the dataset
        --skip_analyse, -a        |   Skip analysis of the results
        --verbosity, -v           |   Verbosity logging level (INFO=20 DEBUG=10)

        --------------------------------------------------------------
        Full traces available at: https://github.com/ComputerNetworks-UFRGS/TraceCollection/tree/master/01_traces

#  Run (all experiments):
`python3 run_sbrc21.py -c sbrc`

# Run (only one scenario)
`python3 main.py`

## Requirements:

`matplotlib 3.4.1`
`tensorflow 2.4.1`
`tqdm 4.60.0`
`numpy 1.18.5`

`keras 2.4.3`
`setuptools 45.2.0`
`h5py 2.10.0`

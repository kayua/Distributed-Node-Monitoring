# Monitor nodes 

Simple implementation nodes monitor using Apache Zookeeper Server



## Commands:


    Python3(main.py):

    Monitor Servers:                            Parameters

        ServerInstall                |   hostname userName password
        ServerStart                  |              -
        ServerUninstall              |              -
        ServerStop                   |              -

    Nodes clients:

        ClientInstall                |   hostname userName password
        ClientAdd                    |   hostname userName password
        ClientRemove                 |   hostname userName password
    
    Monitor:

        AllState                     |              -
        ClientState                  |   hostname userName password
        MonitorSettings              |              -

## Requirements:

`matplotlib 3.4.1`
`tensorflow 2.4.1`
`tqdm 4.60.0`
`numpy 1.18.5`

`keras 2.4.3`
`setuptools 45.2.0`
`h5py 2.10.0`

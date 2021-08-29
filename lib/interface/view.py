from pyfiglet import Figlet


class View:

    def __init__(self, title='Monitor Nodes'):

        self.title = title

    def print_view(self):

        f = Figlet(font='slant')
        print(f.renderText(self.title))


def print_help():

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
    print("     - MonitoSettings    \n\n")
    print("")
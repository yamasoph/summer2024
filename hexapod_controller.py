from pipython import GCSDevice
import keyboard
from rich import print

pidevice = GCSDevice('C-887')
pidevice.InterfaceSetupDlg()
print(pidevice.qIDN())
print(pidevice.qPOS())
print("[yellow]Use the up & down arrows to change the hexapod, hit the right and left arrows to change the increment, hit spacebar to reset and choose a new axis.[/yellow]")

def hexfunc():
    axes = ["X", "Y", "Z", "U", "V", "W"]
    inc = 0.001 #default
   
    while True:
        try:
            #hit either 1,2,3,4,5,6 for corresponding axes
            print("[yellow]Select axis to move (1-6):[/yellow]")
            ax = int(input()) - 1
            if ax < 0 or ax >= len(axes):
                print("[red]Invalid axis number. Please enter a number between 1 and 6.[/red]")
                continue
            #print axis selected for confirmation
            print(f"[bold blue]Selected axis: {axes[ax]}[/bold blue]")

            while True:
                pos = pidevice.qPOS(axes[ax])
                dict_pos = pos[axes[ax]]
               
                if keyboard.is_pressed("up"):
                    #if up key is pressed add specfici increment to axis position it was just in
                    new_pos = dict_pos + inc
                    pidevice.MOV(axes[ax], new_pos)
                    #print current position for all axes
                    print(pidevice.qPOS())                
                elif keyboard.is_pressed("down"):
                    new_neg_pos = dict_pos - inc
                    pidevice.MOV(axes[ax], new_neg_pos)
                    print(pidevice.qPOS())
                elif keyboard.is_pressed("right"):
                    inc += 0.001
                    print(f"[grey]Increment: {inc}[/grey]")
                elif keyboard.is_pressed("left"):
                    inc -= 0.001
                    print(f"[grey]Increment: {inc}[/grey]")
                elif keyboard.is_pressed("space"):
                    #restart function basically to user input for axis
                    break
        except ValueError:
            print("[red]Please enter a valid number.[/red]")

hexfunc()

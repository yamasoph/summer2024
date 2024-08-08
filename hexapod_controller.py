from pipython import GCSDevice
import keyboard

pidevice = GCSDevice('C-887')
pidevice.InterfaceSetupDlg()
print(pidevice.qIDN())
print(pidevice.qPOS())

def hexfunc():
    axes = ["X", "Y", "Z", "U", "V", "W"]
    while True:
        try:
            #hit either 1,2,3,4,5,6 for corresponding axes
            ax = int(input("Select axis to move (1-6): ")) - 1
            if ax < 0 or ax >= len(axes):
                print("Invalid axis number. Please enter a number between 1 and 6.")
                continue
            #print axis selected for confirmation
            print("Axis is: " + str(ax + 1) + " = " + axes[ax])

            #specify amount of incrememntation
            inc = float(input("Input specific increment: "))
            print("Increment chosen: " + str(inc))

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
                elif keyboard.is_pressed("space"):
                    #restart function basically to user input for axis
                    break
        except ValueError:
            print("Please enter a valid number.")

hexfunc()

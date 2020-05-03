from relay_lib_seeed import *
from time import *


print ("Hello World")
print ('Dies ist die zweite Zeile')
for ii in range(0,20):
    relay_on(1)
    sleep(0.05)
    relay_off(1)
    sleep(0.05)
    relay_on(2)
    sleep(0.05)
    relay_off(2)
    sleep(0.05)
    relay_on(3)
    sleep(0.05)
    relay_off(3)
    sleep(0.05)
    relay_on(4)
    sleep(0.05)
    relay_off(4)

print("Nun schalten wir alles 'off'")
relay_all_off()
print("Relay Test - End of Program")

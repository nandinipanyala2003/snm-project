import random

def generateotp():  
    otp = ''
    up = [chr(i) for i in range(ord('A'), ord('Z')+1)]
    lc = [chr(i) for i in range(ord('a'), ord('z')+1)]
    for i in range(2):
        otp = otp + random.choice(up) + str(random.randint(0,9)) + random.choice(lc)
    return otp  

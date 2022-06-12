from PIL import Image
import numpy as np
import math
import sys
import os

def convertDNA(x):
    res=""
    while len(x) > 0:
        c=x[:2]
        x=x[2:]
        if c == "00":
            res += "A"
        elif c == "11":
            res += "T"
        elif c == "01":
            res += "G"
        else:
            res += "C"
    return res

def convert8intDNA(x):
    res=""
    x_bin=bin(x)[2:]
    if len(x_bin) < 8:
        x_bin = ("0" * (8-len(x_bin))) + x_bin
    while len(x_bin) > 0:
        c=x_bin[:2]
        x_bin=x_bin[2:]
        if c == "00":
            res += "A"
        elif c == "11":
            res += "T"
        elif c == "01":
            res += "G"
        else:
            res += "C"
    return res

def convertDNA8int(x):
    res = ""
    while len(x) > 0:
        c = x[0]
        x = x[1:]
        if c == "A":
            res += "00"
        elif c == "T":
            res += "11"
        elif c == "G":
            res += "01"
        else:
            res += "10"
    return int(res, 2)

def attack(attackedImg="Images\\encrypted_example.png", keyMask="Images\\confusion_encrypted.png", firstKey=""):

    im = Image.open(f"{attackedImg}")
    arr = np.array(im)

    imEnc = Image.open(keyMask)
    arrEnc = np.array(imEnc)
    secondKey=""

    for i in range(imEnc.size[0]-1, -1, -1):    #reverse XOR
        for j in range(imEnc.size[1]-1, -1 ,-1):
            for k in range(2, -1, -1):
                if i==0 and j==0:
                    break
                if k-1 < 0:
                    if j-1 < 0:
                        arrEnc[i][j][k]=int(bin(arrEnc[i][j][k]^arrEnc[i-1][imEnc.size[1]-1][2]),2)
                    else:
                        arrEnc[i][j][k]=int(bin(arrEnc[i][j][k]^arrEnc[i][j-1][2]),2)
                else:
                    arrEnc[i][j][k]=int(bin(arrEnc[i][j][k]^arrEnc[i][j][k-1]),2)

    for i in range(imEnc.size[0]): #extracting key 2
        for j in range(imEnc.size[1]):
            for k in range(3):
                secondKey+=convert8intDNA(arrEnc[i][j][k])
                
    ### decrypting image ###
    for i in range(im.size[0]-1, -1, -1):    #reverse XOR
        for j in range(im.size[1]-1, -1 ,-1):
            for k in range(2, -1, -1):
                if i==0 and j==0:
                    break
                if k-1 < 0:
                    if j-1 < 0:
                        arr[i][j][k]=int(bin(arr[i][j][k]^arr[i-1][im.size[1]-1][2]),2)
                    else:
                        arr[i][j][k]=int(bin(arr[i][j][k]^arr[i][j-1][2]),2)
                else:
                    arr[i][j][k]=int(bin(arr[i][j][k]^arr[i][j][k-1]),2)

    dnaS=secondKey

    for i in range(im.size[0]):
        for j in range(im.size[1]):
            for k in range(3):
                tmpval=convert8intDNA(arr[i][j][k])
                tmpres=""
                for q in range(4):
                    tmpaddstr=tmpval[q]+dnaS[0]
                    dnaS=dnaS[1:]
                    if tmpaddstr == "AA":
                        tmpres += "A"
                    elif tmpaddstr == "AG":
                        tmpres += "T"
                    elif tmpaddstr == "AC":
                        tmpres += "C"
                    elif tmpaddstr == "AT":
                        tmpres += "G"
                    elif tmpaddstr == "GA":
                        tmpres += "G"
                    elif tmpaddstr == "GG":
                        tmpres += "A"
                    elif tmpaddstr == "GC":
                        tmpres += "T"
                    elif tmpaddstr == "GT":
                        tmpres += "C"
                    elif tmpaddstr == "CA":
                        tmpres += "C"
                    elif tmpaddstr == "CG":
                        tmpres += "G"
                    elif tmpaddstr == "CC":
                        tmpres += "A"
                    elif tmpaddstr == "CT":
                        tmpres += "T"
                    elif tmpaddstr == "TA":
                        tmpres += "T"
                    elif tmpaddstr == "TG":
                        tmpres += "C"
                    elif tmpaddstr == "TC":
                        tmpres += "G"
                    else:
                        tmpres += "A"
                arr[i][j][k]=convertDNA8int(tmpres)

    seq1=firstKey

    try:
        flatArr=arr.reshape(im.size[0]*im.size[1],3)
    except ValueError:
        flatArr=arr.reshape(im.size[0]*im.size[1],4)

    for i in range(seq1.count("1")):
        pos=seq1.rfind("1")
        seq1=seq1[:pos]
        temp=np.copy(flatArr[0])
        for j in range(pos):
            flatArr[j]=flatArr[j+1]
        flatArr[pos]=temp

    im2 = Image.fromarray(arr)
    im2.save(f"{attackedImg[:-4]}_wydobyty.png")
    im2.close()

def main():
    if len(sys.argv) == 1:
        attack()
    elif len(sys.argv) == 3 or len(sys.argv) == 4:
        if not os.path.isfile(sys.argv[1]) or not os.path.isfile(sys.argv[2]):
            print("At least one of given files does not exist")
            exit(1)
        if len(sys.argv) == 3:           
            attack(sys.argv[1], sys.argv[2])
        else:
            attack(sys.argv[1], sys.argv[2], sys.argv[3])
    


if __name__ == "__main__":
    main()

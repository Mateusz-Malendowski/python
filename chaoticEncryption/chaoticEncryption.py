from PIL import Image
import numpy as np
import math
import sys
import os

def logistic(x, mi):
    return mi*x*(1-x)

def PRBG(x,y):
    if x>y:
        return 1
    else:
        return 0

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

def encrypt(filename, init_mi1, init_x1, init_mi2, init_x2):
    im = Image.open(f"{filename}.png")
    arr = np.array(im)
    im.close()

    seq=""
    for i in range(im.size[0]*im.size[1]):
        init_x1=logistic(init_x1,init_mi1)
        init_x2=logistic(init_x2,init_mi2)
        seq=seq+str(PRBG(init_x1,init_x2))
        
    try:
        flatArr=arr.reshape(im.size[0]*im.size[1],3)
    except ValueError:
        flatArr=arr.reshape(im.size[0]*im.size[1],4)

    for i in range(len(seq)):
        if seq[i]=="1":
            temp=np.copy(flatArr[i])
            for j in range(i, 0, -1):
                flatArr[j]=flatArr[j-1]
            flatArr[0]=temp

    subs_seq=""
    for i in range((im.size[0]*im.size[1]*8*3)+2):
        init_x1=logistic(init_x1,init_mi1)
        init_x2=logistic(init_x2,init_mi2)
        subs_seq=subs_seq+str(PRBG(init_x1,init_x2))
    dnaS=convertDNA(subs_seq)

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
                        tmpres += "G"
                    elif tmpaddstr == "AC":
                        tmpres += "C"
                    elif tmpaddstr == "AT":
                        tmpres += "T"
                    elif tmpaddstr == "GA":
                        tmpres += "G"
                    elif tmpaddstr == "CA":
                        tmpres += "C"
                    elif tmpaddstr == "TA":
                        tmpres += "T"
                    elif tmpaddstr == "GG":
                        tmpres += "C"
                    elif tmpaddstr == "GC":
                        tmpres += "T"
                    elif tmpaddstr == "GT":
                        tmpres += "A"
                    elif tmpaddstr == "CG":
                        tmpres += "T"
                    elif tmpaddstr == "TG":
                        tmpres += "A"
                    elif tmpaddstr == "CC":
                        tmpres += "A"
                    elif tmpaddstr == "CT":
                        tmpres += "G"
                    elif tmpaddstr == "TC":
                        tmpres += "G"
                    else:
                        tmpres += "C"
                arr[i][j][k]=convertDNA8int(tmpres)

    prev=arr[0][0][2]
    for i in range(im.size[0]):
        for j in range(im.size[1]):
            for k in range(3):
                if i==0 and j==0:
                    continue
                arr[i][j][k]=int(bin(arr[i][j][k]^prev),2)
                prev=arr[i][j][k]
                
    im2 = Image.fromarray(arr)
    im2.show()
    im2.save(f"{filename}_zaszyfrowany.png")
    im2.close()

def decrypt(filename, init_mi1, init_x1, init_mi2, init_x2):
    im = Image.open(f"{filename}.png")
    arr = np.array(im)
    im.close()

    seq1=""
    for i in range(im.size[0]*im.size[1]):
        init_x1=logistic(init_x1,init_mi1)
        init_x2=logistic(init_x2,init_mi2)
        seq1=seq1+str(PRBG(init_x1,init_x2))

    for i in range(im.size[0]-1, -1, -1):
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

    subs_seq=""
    for i in range((im.size[0]*im.size[1]*8*3)+2):
        init_x1=logistic(init_x1,init_mi1)
        init_x2=logistic(init_x2,init_mi2)
        subs_seq=subs_seq+str(PRBG(init_x1,init_x2))
    dnaS=convertDNA(subs_seq)

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
    im2.show()
    im2.save(f"{filename}_odszyfrowany.png")
    im2.close()


def main():
    if len(sys.argv) != 7:
        print("6 parameters needed: filenameWithoutExtension, mode, mi0, x0, mi1, y0\possible modes: \"e\" encrypting, \"d\" decrypting")
        
    elif not os.path.isfile(sys.argv[1]+".png"):
        print("File does not exist")
        
    try:
        mi0=float(sys.argv[3])
        x0=float(sys.argv[4])
        mi1=float(sys.argv[5])
        y0=float(sys.argv[6])
            
        if mi0 < 3.65 or mi1 < 3.65 or mi0 > 3.95 or mi1 > 3.95 or x0 < 0 or y0 < 0 or x0 > 1 or y0 > 1:
            print("mi0 i mi1 have to be between (3.65, 3.95)\nx0 and y0 between (0, 1)")
            exit(1)
                
        if sys.argv[2].upper() == "E":
            encrypt(sys.argv[1], mi0, x0, mi1, y0)
            except ValueError:
                print("Incorrect parameter format, example: file e 3.73 0.17062701 3.88883 0.66897")
        
        elif sys.argv[2].upper() == "D":
            decrypt(sys.argv[1], mi0, x0, mi1, y0)
            except ValueError:
                print("Incorrect parameter format, example: file d 3.73 0.17062701 3.88883 0.66897")

if __name__ == "__main__":
    main()

Implementation of algorithm presented in ["A light weight secure image encryption scheme based on chaos & DNA computing"](https://www.sciencedirect.com/science/article/pii/S1319157816300027)
and possible attack on this algorithm. This was part of my bachelor's thesis.

chaoticEncryption.py is implementation of said algorithm, while attack.py is my proposed known-plaintext attack on this algorithm.

Both programs transform data on **pixel** basis.

chaoticEncryption.py usage:
python .\chaoticEncryption.py fileWithoutExtension, mode, mi0, x0, mi1, y0
Modes:
E - encryption
D - decryption

Parameters have to be between
mi ∊ (3.65, 3.95)
x,y ∊ (0, 1)

Example values:
mi0 = 3.73
x0 = 0.17062701
mi1 = 3.88883
y0 = 0.66897

Example file execution:
python .\chaoticEncryption.py file e 3.73 0.17062701 3.88883 0.66897
python .\chaoticEncryption.py encrypted_file d 3.73 0.17062701 3.88883 0.66897

attack.py usage:
python .\attack.py

Optional parameters:
First param    - path to attacked file
Second param   - encrypted mask used to extract first key
Third param    - extraced key

Example file execution:
python .\attack.py
python .\attack.py Images\encrypted_example.png Images\confusion_encrypted.png
python .\attack.py Images\encrypted_example.png Images\confusion_encrypted.png 0101101001100101

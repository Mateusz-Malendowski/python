from hdwallet import BIP44HDWallet
from hdwallet.cryptocurrencies import EthereumMainnet
from hdwallet.derivations import BIP44Derivation
from hdwallet.utils import generate_mnemonic
from typing import Optional
from re import findall
import urllib.request, urllib.error, urllib.parse

KEY=""  #your key here

addressList=[]
counter=0
while True:
    MNEMONIC: str = generate_mnemonic(language="english", strength=128)
    PASSPHRASE: Optional[str] = None
    bip44_hdwallet: BIP44HDWallet = BIP44HDWallet(cryptocurrency=EthereumMainnet)
    bip44_hdwallet.from_mnemonic(
        mnemonic=MNEMONIC, language="english", passphrase=PASSPHRASE
    )
    bip44_hdwallet.clean_derivation()

    print("Mnemonic:", bip44_hdwallet.mnemonic())
    addressList.clear()
    url="https://api.etherscan.io/api?module=account&action=balancemulti&address="
    for address_index in range(20):
        bip44_derivation: BIP44Derivation = BIP44Derivation(
            cryptocurrency=EthereumMainnet, account=0, change=False, address=address_index
        )
        bip44_hdwallet.from_path(path=bip44_derivation)
        addressList.append((bip44_hdwallet.address(),bip44_hdwallet.path(),bip44_hdwallet.private_key(),bip44_hdwallet.mnemonic()))
        url+=bip44_hdwallet.address()+","
               
        
        bip44_hdwallet.clean_derivation()

    url = url[:-1]
    url+=f"&tag=latest&apikey={KEY}"

    response = urllib.request.urlopen(url)
    webContent = response.read()
    if len(findall(r'balance":"0"',webContent.decode("utf-8"))) < 20:
        print("Found:")
        print(addressList)
        break
    else:
        print(f"{counter}. Checked addresses: {counter*20}")
        counter+=1


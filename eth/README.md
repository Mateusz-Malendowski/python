Simple ethereum address scanner which generates random wallet and then, based on Etherscan.io API it checks whether it's balance is greater than 0.

It serves purpose of showing that even though anyone can try to generate multiple wallets in hope that it was already used by someone and that it contains money, it's not something that's feasible within any reasonable timeframe due to size of Ethereum's address size, which is 2<sup>160</sup>

This script most likely could run much faster if instead of Etherscan API it queried your own Ethereum node directly, but setting up whole node requires much more effort than writing simple script just to demonstrate a concept. 

To use it you need to insert your API key into KEY variable and then run the script.

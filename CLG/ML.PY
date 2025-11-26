print("Name: FOUZAN NASEER")
print("RRN: 230171601045")

from Crypto.PublicKey import DSA
from Crypto.Signature import DSS
from Crypto.Hash import SHA256

message = input("Enter the message to be signed: ").encode()
key = DSA.generate(1024)
public_key = key.publickey()
hash_obj = SHA256.new(message)
signer = DSS.new(key, 'fips-186-3')
signature = signer.sign(hash_obj)
verifier = DSS.new(public_key, 'fips-186-3')

try:
    verifier.verify(hash_obj, signature)
    print("Signature is valid.")
except ValueError:
    print("Signature is invalid.")


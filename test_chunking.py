from backend.app.services.chunk_service import (
    fixed_chunking,
    recursive_chunking,
    token_chunking
)


text = """
Object oriented programming is a programming paradigm based
on objects and classes. Classes define the structure and
behavior of objects.

Inheritance allows a class to acquire properties and methods
from another class.

Polymorphism allows different objects to respond differently
to the same interface.

Encapsulation bundles data and methods together and controls
access to internal state.
"""


chunks = token_chunking(
    text,
    chunk_size=20,
    overlap=5
)


print("Total chunks:", len(chunks))

for i, chunk in enumerate(chunks):

    print("\n--------------------")
    print("CHUNK", i)
    print("--------------------")

    print(chunk)
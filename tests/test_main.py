import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import hello_world

def test_hello_world():
    assert hello_world() == "Olá, mundo do Python!"

if __name__ == "__main__":
    test_hello_world()
    print("Teste passou!")


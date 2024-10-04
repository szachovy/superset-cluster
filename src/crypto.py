import os
import base64
import random
import string
# from crypto import X509Req
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import Name, NameAttribute
import cryptography.x509 as x509
import os
import datetime

class OpenSSL:
    @staticmethod
    def generate_mysql_root_password():
        return base64.b64encode(os.urandom(16)).decode('utf-8')

    @staticmethod
    def generate_mysql_superset_password():
        return ''.join(random.choice(string.ascii_lowercase) for _ in range(12))

    @staticmethod
    def generate_superset_secret_key():
        return base64.b64encode(os.urandom(42)).decode('utf-8')
    
    @staticmethod
    def generate_private_key():
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

    @staticmethod
    def generate_csr(common_name: str, private_key):
        return x509.CertificateSigningRequestBuilder().subject_name(
                x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, common_name)])
            ).sign(
                private_key, hashes.SHA256(), default_backend()
        )

    @staticmethod
    def generate_certificate(common_name: str, private_key: str, ca_key: str | None = None):
        return x509.CertificateBuilder().subject_name(
                x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
            ).issuer_name(
                x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).sign(
                ca_key if ca_key else private_key, hashes.SHA256(), default_backend()
        )

    @staticmethod
    def deserialization(thing):
        if isinstance(thing, rsa.RSAPrivateKey):
            return thing.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
        return thing.public_bytes(serialization.Encoding.PEM).decode('utf-8')

    # @staticmethod
    # def generate_certificate(private_key: str, common_name: str):
    #     return x509.CertificateBuilder().subject_name(
    #         csr.subject # Use subject from the CSR
    #     ).issuer_name(
    #         ca_cert.subject   # Use issuer from the CA certificate
    #     ).public_key(
    #         csr.public_key()  # Use public key from the CSR
    #     ).serial_number(
    #         x509.random_serial_number()  # Generate a random serial number
    #     ).not_valid_before(
    #         datetime.datetime.utcnow()
    #     ).not_valid_after(
    #         datetime.datetime.utcnow()
    #     ).sign(
    #         ca_private_key, hashes.SHA256(), default_backend()  # Sign with the CA private key
    #     )
    # )

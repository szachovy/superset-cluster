
import base64
import cryptography
import cryptography.hazmat.backends
import cryptography.hazmat.primitives.asymmetric.ed25519
import cryptography.x509
import datetime
import os
import random
import string


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
    def generate_private_key() -> cryptography.hazmat.bindings._rust.openssl.ed25519.Ed25519PrivateKey:
        return cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PrivateKey.generate()

    @staticmethod
    def generate_csr(common_name: str, private_key: cryptography.hazmat.bindings._rust.openssl.ed25519.Ed25519PrivateKey) -> cryptography.hazmat.bindings._rust.x509.CertificateSigningRequest:
        return cryptography.x509.CertificateSigningRequestBuilder().subject_name(
                cryptography.x509.Name([cryptography.x509.NameAttribute(cryptography.x509.oid.NameOID.COMMON_NAME, common_name)])
            ).sign(
                private_key, algorithm=None
        )

    @staticmethod
    def generate_certificate(common_name: str, private_key: cryptography.hazmat.bindings._rust.x509.CertificateSigningRequest | cryptography.hazmat.bindings._rust.openssl.ed25519.Ed25519PrivateKey, ca_key: cryptography.hazmat.bindings._rust.openssl.ed25519.Ed25519PrivateKey | None = None) -> cryptography.hazmat.bindings._rust.x509.Certificate:
        return cryptography.x509.CertificateBuilder().subject_name(
                cryptography.x509.Name([cryptography.x509.NameAttribute(cryptography.x509.oid.NameOID.COMMON_NAME, common_name)])
            ).issuer_name(
                cryptography.x509.Name([cryptography.x509.NameAttribute(cryptography.x509.oid.NameOID.COMMON_NAME, common_name)])
            ).public_key(
                private_key.public_key()
            ).serial_number(
                cryptography.x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).sign(
                ca_key if ca_key else private_key, algorithm=None
        )

    @staticmethod
    def deserialization(pki: cryptography.hazmat.bindings._rust.openssl.ed25519.Ed25519PrivateKey | cryptography.hazmat.bindings._rust.x509.CertificateSigningRequest | cryptography.hazmat.bindings._rust.x509.Certificate) -> str:
        if isinstance(pki, cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PrivateKey):
            return pki.private_bytes(
                encoding=cryptography.hazmat.primitives.serialization.Encoding.PEM,
                format=cryptography.hazmat.primitives.serialization.PrivateFormat.PKCS8,
                encryption_algorithm=cryptography.hazmat.primitives.serialization.NoEncryption()
            ).decode('utf-8')
        return pki.public_bytes(cryptography.hazmat.primitives.serialization.Encoding.PEM).decode('utf-8')

# import crypto
# obj = crypto.OpenSSL()
# a = obj.generate_private_key()
# b = obj.generate_csr('asd', a)
# c = obj.generate_certificate('asd', b, a)
# print(obj.deserialize(a))
# print(obj.deserialize(b))
# print(obj.deserialize(c))

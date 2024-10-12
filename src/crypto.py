"""
temp
"""

# pylint: disable=c-extension-no-member

import base64
import datetime
import os
import random
import string
import cryptography
import cryptography.hazmat.backends
import cryptography.hazmat.primitives.hashes
import cryptography.hazmat.primitives.asymmetric.rsa
import cryptography.x509


class OpenSSL:
    @staticmethod
    def generate_mysql_root_password() -> str:
        return base64.b64encode(os.urandom(16)).decode('utf-8')

    @staticmethod
    def generate_mysql_superset_password() -> str:
        return "".join(random.choice(string.ascii_lowercase) for _ in range(12))

    @staticmethod
    def generate_superset_secret_key() -> str:
        return base64.b64encode(os.urandom(42)).decode('utf-8')

    @staticmethod
    def generate_private_key() -> cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey:
        return cryptography.hazmat.primitives.asymmetric.rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=cryptography.hazmat.backends.default_backend()
        )

    @staticmethod
    def generate_csr(common_name: str,
                     private_key: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey
                     ) -> cryptography.x509.base.CertificateSigningRequest:
        return cryptography.x509.CertificateSigningRequestBuilder().subject_name(
                cryptography.x509.Name(
                    [
                        cryptography.x509.NameAttribute(cryptography.x509.oid.NameOID.COMMON_NAME, common_name)
                    ]
                )
            ).sign(
                private_key,
                algorithm=cryptography.hazmat.primitives.hashes.SHA256(),
                backend=cryptography.hazmat.backends.default_backend()
        )

    @staticmethod
    def generate_certificate(
        common_name: str,
        private_key: cryptography.x509.base.CertificateSigningRequest |
        cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey,
        ca_key: cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey | None = None
    ) -> cryptography.x509.base.Certificate:
        return cryptography.x509.CertificateBuilder().subject_name(
                cryptography.x509.Name(
                    [
                        cryptography.x509.NameAttribute(cryptography.x509.oid.NameOID.COMMON_NAME, common_name)
                    ]
                )
            ).issuer_name(
                cryptography.x509.Name(
                    [
                        cryptography.x509.NameAttribute(cryptography.x509.oid.NameOID.COMMON_NAME, common_name)
                    ]
                )
            ).public_key(
                private_key.public_key()
            ).serial_number(
                cryptography.x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=365)
            ).sign(
                ca_key if ca_key else private_key,  # type: ignore[arg-type]
                algorithm=cryptography.hazmat.primitives.hashes.SHA256(),
                backend=cryptography.hazmat.backends.default_backend()
        )

    @staticmethod
    def deserialization(pki:
                        cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey |
                        cryptography.x509.base.CertificateSigningRequest |
                        cryptography.x509.base.Certificate |
                        None) -> str:
        if isinstance(pki, cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey):
            return pki.private_bytes(
                encoding=cryptography.hazmat.primitives.serialization.Encoding.PEM,
                format=cryptography.hazmat.primitives.serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=cryptography.hazmat.primitives.serialization.NoEncryption()
            ).decode('utf-8')
        if pki:
            return pki.public_bytes(cryptography.hazmat.primitives.serialization.Encoding.PEM).decode('utf-8')
        raise ValueError('Cannot deserialize certificate, error while generation')

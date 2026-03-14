from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime

# Generate CA private key
ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# Generate CA certificate
ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "DePIN-Guard-CA")])
ca_cert = (
    x509.CertificateBuilder()
    .subject_name(ca_name)
    .issuer_name(ca_name)
    .public_key(ca_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
    .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    .sign(ca_key, hashes.SHA256())
)

# Generate Server private key
server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# Generate Server certificate signed by CA
server_cert = (
    x509.CertificateBuilder()
    .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")]))
    .issuer_name(ca_name)
    .public_key(server_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
    .sign(ca_key, hashes.SHA256())
)

# Save ca.crt
with open("ca.crt", "wb") as f:
    f.write(ca_cert.public_bytes(serialization.Encoding.PEM))

# Save server.crt
with open("server.crt", "wb") as f:
    f.write(server_cert.public_bytes(serialization.Encoding.PEM))

# Save server.key
with open("server.key", "wb") as f:
    f.write(server_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption()
    ))

print("✅ Certificates generated: ca.crt, server.crt, server.key")
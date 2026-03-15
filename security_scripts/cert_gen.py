from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime

# ─── Load existing CA to sign client cert ───
with open("docker/certs/ca.crt", "rb") as f:
    ca_cert = x509.load_pem_x509_certificate(f.read())

# ─── Generate CLIENT private key ───
client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# ─── Generate CLIENT certificate signed by existing CA ───
client_cert = (
    x509.CertificateBuilder()
    .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "depin-client")]))
    .issuer_name(ca_cert.subject)
    .public_key(client_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
    .sign(client_key, hashes.SHA256())
)

# ─── Save Client certs ───
with open("security_scripts/client.crt", "wb") as f:
    f.write(client_cert.public_bytes(serialization.Encoding.PEM))

with open("security_scripts/client.key", "wb") as f:
    f.write(client_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption()
    ))

print("✅ Client certificates generated: client.crt, client.key")
print("📁 Saved in security_scripts/ folder")
print("⚠️  Share with Vineet directly — DO NOT push client.key to GitHub!")
# crypto_utils.py
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64
from typing import Tuple

def generate_key_pair() -> Tuple[str, str]:
    """生成RSA密钥对，返回(private_key, public_key)"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem.decode('utf-8'), public_pem.decode('utf-8')

def encrypt_message(message: str, public_key_pem: str) -> str:
    """使用公钥加密消息"""
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode('utf-8'),
        backend=default_backend()
    )
    
    # 生成AES密钥
    key = os.urandom(32)
    iv = os.urandom(16)
    
    # 使用AES加密消息
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    # 对消息进行PKCS7填充
    padded_message = message.encode('utf-8')
    padding_length = 16 - len(padded_message) % 16
    padded_message += bytes([padding_length] * padding_length)
    
    encrypted_message = encryptor.update(padded_message) + encryptor.finalize()
    
    # 使用RSA加密AES密钥
    encrypted_key = public_key.encrypt(
        key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # 组合并编码
    combined_data = encrypted_key + iv + encrypted_message
    return base64.b64encode(combined_data).decode('utf-8')

def decrypt_message(encrypted_data: str, private_key_pem: str) -> str:
    """使用私钥解密消息"""
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode('utf-8'),
        password=None,
        backend=default_backend()
    )
    
    # 解码数据
    data = base64.b64decode(encrypted_data.encode('utf-8'))
    
    # 分离各部分
    encrypted_key = data[:256]  # RSA 2048位密钥加密后的长度
    iv = data[256:272]  # AES IV 长度
    encrypted_message = data[272:]
    
    # 解密AES密钥
    key = private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # 解密消息
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    padded_message = decryptor.update(encrypted_message) + decryptor.finalize()
    
    # 去除PKCS7填充
    padding_length = padded_message[-1]
    message = padded_message[:-padding_length]
    
    return message.decode('utf-8')
# NGINX + AWS Nitro Enclave TLS Proxy Setup (Full Setup Instructions)

These instructions document the **complete process** for building a new
proxy server that terminates TLS using **AWS Nitro Enclaves + ACM** and
routes traffic to workshop EC2 instances running Jupyter.

The proxy is an **Amazon Linux 2023** instance configured with:

-   nginx
-   aws-nitro-enclaves-cli
-   aws-nitro-enclaves-acm
-   pkcs11 TLS integration
-   ACM certificate injection via enclave

The result is:

    Internet
      ↓
    Route53 DNS
      ↓
    Elastic IP
      ↓
    NGINX
      ↓
    TLS private key inside Nitro Enclave
      ↓
    Reverse proxy
      ↓
    Workshop EC2 instances (Jupyter)
